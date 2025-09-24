import os, requests
from lxml import etree
import logging
from typing import Dict, Any, List
from app.parsers.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

NC_URL  = os.getenv("NC_WEBDAV_URL", "")
NC_USER = os.getenv("NC_USER", "")
NC_PASS = os.getenv("NC_PASS", "")
NC_EXTS = [e.strip() for e in os.getenv("NC_EXTS", ".txt,.md,.pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp").split(",")]

def list_webdav(url: str) -> list[dict]:
    """
    返回 [{href, is_dir, displayname, getcontenttype}] 列表
    """
    headers = {"Depth": "1"}
    body = """<?xml version="1.0"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:displayname/>
        <d:resourcetype/>
        <d:getcontenttype/>
      </d:prop>
    </d:propfind>"""
    resp = requests.request("PROPFIND", url, data=body, headers=headers, auth=(NC_USER, NC_PASS))
    resp.raise_for_status()
    root = etree.fromstring(resp.content)
    ns = {"d": "DAV:"}
    items = []
    for resp_el in root.findall("d:response", ns):
        href = resp_el.findtext("d:href", namespaces=ns)
        propstat = resp_el.find("d:propstat", ns)
        if propstat is None:
            continue
        prop = propstat.find("d:prop", ns)
        if prop is None:
            continue
        displayname = prop.findtext("d:displayname", namespaces=ns) or href
        rtype = prop.find("d:resourcetype", ns)
        is_dir = rtype is not None and rtype.find("d:collection", ns) is not None
        ctype = prop.findtext("d:getcontenttype", namespaces=ns) or ""
        items.append({"href": href, "is_dir": is_dir, "displayname": displayname, "getcontenttype": ctype})
    return items

def download_text(url: str) -> str:
    """下载纯文本文件，自动处理编码"""
    resp = requests.get(url, auth=(NC_USER, NC_PASS))
    resp.raise_for_status()
    
    # 检查响应编码
    if resp.encoding is None:
        resp.encoding = 'utf-8'
    
    # 如果编码检测失败，尝试常见编码
    try:
        return resp.text
    except UnicodeDecodeError:
        # 尝试其他编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
            try:
                return resp.content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，使用错误处理
        return resp.content.decode('utf-8', errors='ignore')

def download_binary(url: str) -> bytes:
    """下载二进制文件"""
    resp = requests.get(url, auth=(NC_USER, NC_PASS))
    resp.raise_for_status()
    return resp.content

def download_and_parse_file(url: str, filename: str, is_initial: bool = False) -> Dict[str, Any]:
    """
    下载并解析文件，支持多种文档格式
    
    Args:
        url: 文件下载 URL
        filename: 文件名
        is_initial: 是否是初始扫描（如果是，图片文件会返回占位符）
        
    Returns:
        解析结果字典，包含 text, metadata 等信息
    """
    try:
        processor = DocumentProcessor()
        
        # 检测文件类型
        file_type = processor.detect_file_type(filename)
        
        if file_type == 'image' and is_initial:
            # 初始扫描时，图片文件返回占位符
            result = {
                "text": f"[图片文件: {filename}] - 内容正在处理中...",
                "metadata": {
                    "detected_type": "image",
                    "processing_status": "pending",
                    "download_url": url
                }
            }
        elif file_type in ['pdf', 'image']:
            # PDF 和图片文件需要下载二进制数据
            file_bytes = download_binary(url)
            result = processor.process_bytes(file_bytes, filename, file_type)
        else:
            # 文本类文件可以直接下载文本
            try:
                text_content = download_text(url)
                result = processor.process_content(text_content, filename, file_type)
            except UnicodeDecodeError:
                # 如果文本下载失败，尝试二进制下载
                file_bytes = download_binary(url)
                result = processor.process_bytes(file_bytes, filename, file_type)
        
        # 添加下载信息到元数据
        if 'metadata' not in result:
            result['metadata'] = {}
        result['metadata']['download_url'] = url
        result['metadata']['webdav_source'] = True
        
        return result
        
    except Exception as e:
        logger.error(f"Error downloading and parsing file {filename} from {url}: {e}")
        return {
            "text": "",
            "metadata": {
                "error": str(e),
                "filename": filename,
                "download_url": url
            },
            "success": False
        }

def scan_inbox() -> List[Dict[str, Any]]:
    """
    扫描 NC_WEBDAV_URL 下第一层文件，支持多种文档格式解析
    返回 [{title, text, source_uri, metadata}]
    """
    if not NC_URL:
        logger.warning("NC_WEBDAV_URL not configured")
        return []

    try:
        entries = list_webdav(NC_URL)
        out = []
        
        for e in entries:
            if e["is_dir"]:
                continue
                
            href = e["href"]
            filename = e["displayname"]
            
            # 只处理指定后缀
            if not any(href.lower().endswith(ext) for ext in NC_EXTS):
                logger.debug(f"Skipping unsupported file: {filename}")
                continue
            
            try:
                # 构建绝对 URL
                abs_url = _build_absolute_url(href)
                
                # 检测文件类型
                processor = DocumentProcessor()
                file_type = processor.detect_file_type(filename)
                
                # 处理文件
                parse_result = download_and_parse_file(abs_url, filename, is_initial=True)
                
                if parse_result.get('success', True) and parse_result.get('text'):
                    # 构建返回结果
                    document = {
                        "title": filename,
                        "text": parse_result['text'],
                        "source_uri": f"nextcloud://{filename}",
                        "metadata": parse_result.get('metadata', {})
                    }
                    
                    # 添加 WebDAV 特定信息
                    document['metadata'].update({
                        "webdav_href": href,
                        "content_type": e.get("getcontenttype", ""),
                        "scan_source": "webdav_inbox"
                    })
                    
                    out.append(document)
                    logger.info(f"Successfully processed file: {filename}")
                else:
                    # 非图片文件：正常同步处理
                    parse_result = download_and_parse_file(abs_url, filename)
                    
                    if parse_result.get('success', True) and parse_result.get('text'):
                        # 构建返回结果
                        document = {
                            "title": filename,
                            "text": parse_result['text'],
                            "source_uri": f"nextcloud://{filename}",
                            "metadata": parse_result.get('metadata', {})
                        }
                        
                        # 添加 WebDAV 特定信息
                        document['metadata'].update({
                            "webdav_href": href,
                            "content_type": e.get("getcontenttype", ""),
                            "scan_source": "webdav_inbox"
                        })
                        
                        out.append(document)
                        logger.info(f"Successfully processed file: {filename}")
                    else:
                        logger.warning(f"Failed to parse file {filename}: {parse_result.get('metadata', {}).get('error', 'Unknown error')}")
                    
            except Exception as ex:
                logger.error(f"Error processing file {filename}: {ex}")
                continue
        
        logger.info(f"Scanned {len(entries)} entries, successfully processed {len(out)} files")
        return out
        
    except Exception as e:
        logger.error(f"Error scanning WebDAV inbox: {e}")
        return []

def _build_absolute_url(href: str) -> str:
    """
    构建绝对 URL
    
    Args:
        href: WebDAV 返回的 href
        
    Returns:
        绝对 URL
    """
    if href.startswith("http"):
        return href
    
    if NC_URL in href:
        return href
    
    # 简化处理：拼接文件名到 NC_URL
    filename = href.split("/")[-1]
    return NC_URL.rstrip("/") + "/" + filename

