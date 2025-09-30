import { 
  FileTextOutlined, 
  FileImageOutlined, 
  FilePdfOutlined,
  FileMarkdownOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileZipOutlined,
  FileOutlined
} from '@ant-design/icons';
import type { CollectionDocument } from '../../types/collection';

interface DocumentItemProps {
  document: CollectionDocument;
  onClick?: () => void;
}

export default function DocumentItem({ document, onClick }: DocumentItemProps) {
  console.log('🚀 DocumentItem component loaded for:', document.title);
  console.log('📋 Document details:', {
    title: document.title,
    modality: document.modality,
    source_uri: document.source_uri,
    created_at: document.created_at
  });

  // 根据文件名获取文件类型图标
  const getFileTypeIcon = (fileName: string, modality: string) => {
    const extension = fileName.toLowerCase().split('.').pop() || '';
    
    // 图片文件
    if (modality === 'image' || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(extension)) {
      return { icon: FileImageOutlined, color: '#52c41a' };
    }
    
    // 文档文件
    switch (extension) {
      case 'pdf':
        return { icon: FilePdfOutlined, color: '#ff4d4f' };
      case 'md':
      case 'markdown':
        return { icon: FileMarkdownOutlined, color: '#1890ff' };
      case 'doc':
      case 'docx':
        return { icon: FileWordOutlined, color: '#1890ff' };
      case 'xls':
      case 'xlsx':
        return { icon: FileExcelOutlined, color: '#52c41a' };
      case 'ppt':
      case 'pptx':
        return { icon: FilePptOutlined, color: '#fa8c16' };
      case 'zip':
      case 'rar':
      case '7z':
        return { icon: FileZipOutlined, color: '#722ed1' };
      case 'txt':
      case 'log':
        return { icon: FileTextOutlined, color: '#666' };
      default:
        return { icon: FileOutlined, color: '#999' };
    }
  };

  // 生成缩略图URL
  const getThumbnailUrl = (sourceUri: string) => {
    console.log(`🔍 Processing source_uri for thumbnail: "${sourceUri}"`);
    
    let fileName = '';
    
    if (sourceUri.includes('webui://')) {
      fileName = sourceUri.replace('webui://', '');
      console.log(`📁 WebUI file extracted: "${fileName}"`);
    } else if (sourceUri.includes('nextcloud://')) {
      fileName = sourceUri.replace('nextcloud://', '');
      console.log(`☁️ Nextcloud file extracted: "${fileName}"`);
    } else {
      // 如果没有协议前缀，直接使用文件名
      fileName = sourceUri;
      console.log(`📄 Direct filename: "${fileName}"`);
    }
    
    if (fileName) {
      // 使用协议相对 URL，自动适配 http/https
      const thumbnailUrl = `//pkb.kmchat.cloud/api/files/thumbnail/${encodeURIComponent(fileName)}`;
      console.log(`🖼️ Generated thumbnail URL: "${thumbnailUrl}"`);
      return thumbnailUrl;
    }
    
    console.log(`❌ No valid filename found for: "${sourceUri}"`);
    return null;
  };

  // 渲染缩略图或图标
  const renderThumbnail = () => {
    const fileTypeInfo = getFileTypeIcon(document.title, document.modality);
    const IconComponent = fileTypeInfo.icon;
    
    console.log(`🎨 Rendering thumbnail for: ${document.title}, modality: ${document.modality}, color: ${fileTypeInfo.color}`);
    
    // 对于图片文件，尝试加载真实缩略图，失败时显示彩色渐变
    if (document.modality === 'image') {
      const thumbnailUrl = getThumbnailUrl(document.source_uri);
      
      if (thumbnailUrl) {
        console.log(`🖼️ Attempting to load thumbnail: ${thumbnailUrl}`);
        return (
          <div style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            backgroundColor: '#f5f5f5'
          }}>
            <img 
              src={thumbnailUrl} 
              alt={document.title} 
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
              onError={(e) => {
                // 如果真实缩略图加载失败，显示彩色渐变回退
                console.log(`❌ Thumbnail failed to load: ${thumbnailUrl}`);
                const target = e.target as HTMLImageElement;
                const parent = target.parentElement;
                if (parent) {
                  parent.innerHTML = `
                    <div style="
                      width: 100%; 
                      height: 100%; 
                      display: flex; 
                      align-items: center; 
                      justify-content: center;
                      background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
                      color: white;
                      font-size: 24px;
                      flex-direction: column;
                      gap: 4px;
                    ">
                      <div style='font-size: 28px;'>🖼️</div>
                      <div style='font-size: 8px; text-align: center; font-weight: 500; text-shadow: 0 1px 2px rgba(0,0,0,0.3); opacity: 0.9;'>
                        ${document.title.split('.').pop()?.toUpperCase() || 'IMG'}
                      </div>
                    </div>
                  `;
                }
              }}
              onLoad={() => {
                console.log(`✅ Thumbnail loaded successfully: ${thumbnailUrl}`);
              }}
            />
          </div>
        );
      } else {
        // 如果没有缩略图URL，使用彩色渐变
        console.log(`🖼️ No thumbnail URL, using placeholder for: ${document.title}`);
        return (
          <div style={{
            width: '100%',
            height: '100%',
            background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '24px',
            flexDirection: 'column',
            gap: '4px'
          }}>
            <div style={{ fontSize: '28px' }}>🖼️</div>
            <div style={{
              fontSize: '8px',
              textAlign: 'center',
              fontWeight: '500',
              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
              opacity: 0.9
            }}>
              {document.title.split('.').pop()?.toUpperCase() || 'IMG'}
            </div>
          </div>
        );
      }
    }
    
    // 显示文件类型图标（带渐变背景）
    const docColors: { [key: string]: string[] } = {
      '#ff4d4f': ['#ff7875', '#ff4d4f'], // PDF - 红色渐变
      '#1890ff': ['#40a9ff', '#1890ff'], // Word/MD - 蓝色渐变
      '#52c41a': ['#73d13d', '#52c41a'], // Excel - 绿色渐变
      '#fa8c16': ['#ffa940', '#fa8c16'], // PPT - 橙色渐变
      '#722ed1': ['#9254de', '#722ed1'], // ZIP - 紫色渐变
      'default': ['#d9d9d9', '#bfbfbf']  // 默认 - 灰色渐变
    };
    
    const colorPair = docColors[fileTypeInfo.color] || docColors['default'];
    
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${colorPair[0]}, ${colorPair[1]})`,
        flexDirection: 'column',
        gap: '4px'
      }}>
        <IconComponent style={{ 
          fontSize: '24px', 
          color: 'white',
          filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
        }} />
        <div style={{
          fontSize: '8px',
          color: 'white',
          textAlign: 'center',
          fontWeight: '500',
          textShadow: '0 1px 2px rgba(0,0,0,0.3)'
        }}>
          {document.title.split('.').pop()?.toUpperCase() || 'FILE'}
        </div>
      </div>
    );
  };

  // 获取来源标签
  const getSourceLabel = (uri: string) => {
    if (uri.startsWith('nextcloud://')) return '云盘';
    if (uri.startsWith('memo://')) return '备忘';
    return '其他';
  };

  // 格式化日期 - 始终显示完整日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    // 始终显示年/月/日格式
    return `${year}/${month}/${day}`;
  };

  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        padding: '16px',
        borderBottom: '1px solid #f0f0f0',
        cursor: 'pointer',
        transition: 'all 0.3s',
        background: '#fff'
      }}
    >
      {/* 缩略图/图标区域 */}
      <div style={{
        width: '120px',
        height: '80px',
        marginRight: '16px',
        borderRadius: '4px',
        overflow: 'hidden'
      }}>
        {renderThumbnail()}
      </div>

      {/* 文档信息区域 */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between'
      }}>
        <div>
          <h3 style={{
            margin: 0,
            fontSize: '16px',
            fontWeight: 'normal',
            color: '#333',
            marginBottom: '8px'
          }}>
            {document.title}
          </h3>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          fontSize: '12px',
          color: '#999'
        }}>
          <span>{getSourceLabel(document.source_uri)}</span>
          <span style={{ margin: '0 8px' }}>·</span>
          <span>{formatDate(document.created_at)}</span>
        </div>
      </div>
    </div>
  );
}