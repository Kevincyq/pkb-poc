# 文件解析问题修复总结

## 问题描述
- PDF和图片文件上传后显示 `parsing_status: 'failed'`
- 错误信息：`Unsupported file type: 附件1：鸿鹄实验室技术规划流程（TPP）V1.0.pdf`

## 根本原因
1. **错误的参数传递**：将文件名当作文件类型传入
   ```python
   # ❌ 错误的调用
   parse_result = processor.process_file(temp_file.name, content.title)
   ```
   这里将 `content.title`（文件名）传给了 `file_type` 参数

2. **文件类型检测不够健壮**：对于包含中文的文件名路径，检测逻辑不够完善

## 修复方案

### 1. 修复参数传递 (tasks.py)
```python
# ✅ 正确的调用
parse_result = processor.process_file(temp_file.name, file_type=None)
```

### 2. 改进文件类型检测 (document_processor.py)
```python
def detect_file_type(self, filename: str) -> str:
    """根据文件名或路径检测文件类型"""
    # 使用 Path 提取文件名和扩展名
    path = Path(filename)
    filename_lower = path.name.lower()
    suffix = path.suffix.lower()
    
    # PDF 文件
    if suffix == '.pdf' or filename_lower.endswith('.pdf'):
        return 'pdf'
    
    # Markdown 文件
    elif suffix in ['.md', '.markdown', '.mdown', '.mkd'] or \
         any(filename_lower.endswith(ext) for ext in ['.md', '.markdown', '.mdown', '.mkd']):
        return 'markdown'
    
    # 图片文件
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'] or \
         any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
        return 'image'
    
    # 其他文本文件
    else:
        logger.warning(f"Could not determine file type for: {filename}, using 'text' as default")
        return 'text'
```

## 完整的文件上传与处理流程

### 上传路径

#### 云盘用户（已授权Google Drive）
1. **文件上传** (`/ingest/upload-smart`)
   - 文件上传到Google Drive的 `PKB-Files` 文件夹
   - 创建Content记录，`storage_provider='google_drive'`
   - 触发 `download_and_parse_cloud_file` 任务

2. **文件下载与解析** (`download_and_parse_cloud_file`)
   - 从Google Drive下载文件到临时目录
   - 使用 `DocumentProcessor.process_file()` 解析文件
   - 根据文件扩展名自动检测文件类型
   - 调用对应的解析器（PDF/Image/Markdown/Text）

3. **内容分块**
   - 将解析的文本内容分块
   - 创建 Chunk 记录

4. **向量化**
   - 异步生成每个chunk的嵌入向量

5. **分类**
   - 快速分类（规则匹配）
   - 精确AI分类（30秒后）

#### 测试用户（无云盘授权）
1. **文件上传** (`/ingest/upload-smart`)
   - 文件保存到本地 `/app/uploads`
   - 创建Content记录，`storage_provider='local'`
   - 触发 `parse_and_chunk_file` 任务

2. **文件解析** (`parse_and_chunk_file`)
   - 直接解析本地文件
   - 后续流程与云盘用户相同

## 修复的文件类型支持

✅ **支持的格式**：
- PDF：`.pdf`
- 图片：`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`
- Markdown：`.md`, `.markdown`
- 文本：`.txt`

❌ **暂不支持**：
- Office文档（`.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`）
- 其他格式

## 测试建议

1. **PDF文件**：上传PDF文件，验证解析成功
2. **图片文件**：上传JPG/PNG图片，验证内容提取成功
3. **中文文件名**：上传包含中文文件名的文件
4. **大文件**：测试超过5MB的文件（会上传到云盘）

## 相关文件修改

1. `backend/app/workers/tasks.py`
   - 修正了 `download_and_parse_cloud_file` 中的文件解析调用

2. `backend/app/parsers/document_processor.py`
   - 改进了 `detect_file_type` 方法，使用 `Path` 正确处理路径和扩展名

