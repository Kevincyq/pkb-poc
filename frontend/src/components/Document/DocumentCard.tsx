import { Card, Tag, Button, message } from 'antd';
import NativeDropdown from '../NativeDropdown';
import { 
  FileTextOutlined, 
  FileImageOutlined, 
  FilePdfOutlined,
  FileMarkdownOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileZipOutlined,
  FileOutlined,
  MoreOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useState, memo } from 'react';
import api from '../../services/api';
import styles from './DocumentCard.module.css';
import { formatDate } from '../../utils/dateUtils';

interface DocumentCardProps {
  id: string;
  title: string;
  modality: 'text' | 'image' | 'pdf';
  thumbnailUrl?: string;
  sourceUri: string;
  createdAt: string;
  categories?: Array<{
    id: string;
    name: string;
    color: string;
    is_system: boolean;
    confidence?: number;
    role?: string;
    source?: string;
  }>;
  onClick?: () => void;
  onDelete?: (id: string) => void;
  isHighlighted?: boolean; // 新增：是否高亮显示
}

function DocumentCard({
  id,
  title,
  modality,
  sourceUri,
  createdAt,
  categories = [],
  onClick,
  onDelete,
  isHighlighted = false
}: DocumentCardProps) {
  console.log('🚀 DocumentCard component loaded for:', title, 'with props:', {
    id, title, modality, sourceUri, createdAt, hasOnClick: !!onClick, hasOnDelete: !!onDelete
  });
  const [isDeleting, setIsDeleting] = useState(false);
  const [thumbnailError, setThumbnailError] = useState(false);
  // 根据文件名获取文件类型图标和显示名称
  const getFileTypeIcon = (fileName: string, modality: string) => {
    const extension = fileName.toLowerCase().split('.').pop() || '';
    
    // 图片文件
    if (modality === 'image' || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(extension)) {
      return { icon: FileImageOutlined, color: '#52c41a', displayName: '图片' };
    }
    
    // 文档文件
    switch (extension) {
      case 'pdf':
        return { icon: FilePdfOutlined, color: '#ff4d4f', displayName: 'PDF' };
      case 'md':
      case 'markdown':
        return { icon: FileMarkdownOutlined, color: '#1890ff', displayName: 'Markdown' };
      case 'doc':
      case 'docx':
        return { icon: FileWordOutlined, color: '#1890ff', displayName: 'Word' };
      case 'xls':
      case 'xlsx':
        return { icon: FileExcelOutlined, color: '#52c41a', displayName: 'Excel' };
      case 'ppt':
      case 'pptx':
        return { icon: FilePptOutlined, color: '#fa8c16', displayName: 'PPT' };
      case 'zip':
      case 'rar':
      case '7z':
        return { icon: FileZipOutlined, color: '#722ed1', displayName: '压缩包' };
      case 'txt':
      case 'log':
        return { icon: FileTextOutlined, color: '#666', displayName: '文本' };
      default:
        return { icon: FileOutlined, color: '#999', displayName: '文件' };
    }
  };

  // 判断来源标签
  const getSourceTag = (uri: string) => {
    if (uri.includes('nextcloud://')) {
      return { text: '云盘', color: 'blue' };
    } else if (uri.includes('webui://')) {
      return { text: 'WebUI', color: 'green' };
    } else if (uri.includes('memo://')) {
      return { text: '备忘', color: 'orange' };
    }
    return { text: '其他', color: 'default' };
  };

  const sourceTag = getSourceTag(sourceUri);

  // 生成缩略图URL（优先使用后端生成的真实缩略图）
  const getThumbnailUrl = (sourceUri: string) => {
    // 重新启用真实缩略图功能
    console.log(`🔍 Getting thumbnail URL for: ${sourceUri}`);
    
    // 确定API基础URL（与api.ts保持一致）
    // 优先使用环境变量，与api.ts的逻辑保持一致
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 
      (window.location.hostname === 'localhost' 
        ? 'http://localhost:8003/api' 
        : 'https://pkb-test.kmchat.cloud/api'
      );
    
    // 如果是webui上传的图片，尝试使用后端缩略图
    if (sourceUri.includes('webui://')) {
      const fileName = sourceUri.replace('webui://', '');
      // 使用实际存储的文件名（从source_uri获取），进行URL编码以处理中文字符
      const thumbnailUrl = `${apiBaseUrl}/files/thumbnail/${encodeURIComponent(fileName)}`;
      console.log(`📸 WebUI thumbnail URL: ${thumbnailUrl}`);
      return thumbnailUrl;
    }
    
    // 如果是nextcloud的图片，也可以尝试生成缩略图
    if (sourceUri.includes('nextcloud://')) {
      const fileName = sourceUri.replace('nextcloud://', '');
      const thumbnailUrl = `${apiBaseUrl}/files/thumbnail/${fileName}`;
      console.log(`☁️ Nextcloud thumbnail URL: ${thumbnailUrl}`);
      return thumbnailUrl;
    }
    
    // ✅ 支持Google Drive文件的缩略图
    if (sourceUri.includes('google_drive://')) {
      const fileId = sourceUri.replace('google_drive://', '');
      const thumbnailUrl = `${apiBaseUrl}/files/thumbnail/${fileId}`;
      console.log(`🗂️ Google Drive thumbnail URL: ${thumbnailUrl}`);
      return thumbnailUrl;
    }
    
    console.log(`❌ No thumbnail URL generated for: ${sourceUri}`);
    return null;
  };

  // 生成简单的颜色缩略图（作为回退方案）
  const generateColorThumbnail = (title: string, modality: string) => {
    // 为图片文件生成彩色渐变背景
    if (modality === 'image') {
      // 基于文件名生成颜色
      const colors = [
        ['#FF6B6B', '#4ECDC4'], // 红到青
        ['#45B7D1', '#96CEB4'], // 蓝到绿
        ['#FECA57', '#FF9FF3'], // 黄到粉
        ['#5F27CD', '#00D2D3'], // 紫到青
        ['#FF9F43', '#10AC84'], // 橙到绿
        ['#EE5A24', '#0097E6'], // 红橙到蓝
        ['#2E86AB', '#A23B72'], // 蓝到紫红
        ['#F38BA8', '#A8DADC']  // 粉到浅蓝
      ];
      
      // 使用文件名的哈希来选择颜色
      let hash = 0;
      for (let i = 0; i < title.length; i++) {
        hash = title.charCodeAt(i) + ((hash << 5) - hash);
      }
      const colorIndex = Math.abs(hash) % colors.length;
      const [color1, color2] = colors[colorIndex];
      
      return {
        background: `linear-gradient(135deg, ${color1}, ${color2})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontSize: '24px',
        fontWeight: 'bold',
        textShadow: '0 1px 3px rgba(0,0,0,0.3)'
      };
    }
    
    return null;
  };

  // 渲染缩略图或图标
  const renderThumbnail = () => {
    const fileTypeInfo = getFileTypeIcon(title, modality);
    const IconComponent = fileTypeInfo.icon;
    
    console.log(`🎨 Rendering thumbnail for: ${title}, modality: ${modality}, color: ${fileTypeInfo.color}`);
    
    // 对于图片文件，优先尝试真实缩略图
    if (modality === 'image') {
      const thumbnailUrl = getThumbnailUrl(sourceUri);
      
      if (thumbnailUrl && !thumbnailError) {
        return (
          <div className={styles.documentThumbnail}>
            <img 
              src={thumbnailUrl} 
              alt={title} 
              className={styles.documentImage}
              onError={() => {
                console.log(`❌ Thumbnail failed to load: ${thumbnailUrl}`);
                setThumbnailError(true);
              }}
              onLoad={() => {
                console.log(`✅ Thumbnail loaded successfully: ${thumbnailUrl}`);
              }}
            />
          </div>
        );
      } else {
        // 如果没有缩略图URL，直接使用彩色渐变
        const colorStyle = generateColorThumbnail(title, modality);
        
        if (colorStyle) {
          return (
            <div className={styles.documentThumbnail} style={colorStyle}>
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{ fontSize: '48px' }}>🖼️</div>
                <div style={{ 
                  fontSize: '12px', 
                  textAlign: 'center',
                  opacity: 0.9,
                  maxWidth: '120px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {title}
                </div>
              </div>
            </div>
          );
        }
      }
    }
    
    // 显示文件类型图标（带渐变背景）
    console.log(`📄 Rendering document icon for: ${title}, color: ${fileTypeInfo.color}`);
    
    const docColors: { [key: string]: string[] } = {
      '#ff4d4f': ['#ff7875', '#ff4d4f'], // PDF - 红色渐变
      '#1890ff': ['#40a9ff', '#1890ff'], // Word/MD - 蓝色渐变
      '#52c41a': ['#73d13d', '#52c41a'], // Excel - 绿色渐变
      '#fa8c16': ['#ffa940', '#fa8c16'], // PPT - 橙色渐变
      '#722ed1': ['#9254de', '#722ed1'], // ZIP - 紫色渐变
      'default': ['#d9d9d9', '#bfbfbf']  // 默认 - 灰色渐变
    };
    
    const colorPair = docColors[fileTypeInfo.color] || docColors['default'];
    console.log(`🎨 Using color pair for ${title}:`, colorPair);
    
    return (
      <div 
        className={styles.documentThumbnail}
        style={{
          background: `linear-gradient(135deg, ${colorPair[0]}, ${colorPair[1]})`
        }}
      >
        <div className={styles.documentIcon}>
          <IconComponent style={{ 
            fontSize: '48px', 
            color: 'white',
            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
          }} />
          <div style={{
            fontSize: '12px',
            color: 'white',
            textAlign: 'center',
            padding: '0 8px',
            fontWeight: '500',
            textShadow: '0 1px 2px rgba(0,0,0,0.3)'
          }}>
            {fileTypeInfo.displayName}
          </div>
        </div>
      </div>
    );
  };

  // 处理删除操作 - 临时简化版本用于调试
  const handleDelete = async () => {
    console.log('🚨 handleDelete function called for document:', title, 'ID:', id);
    
    // 临时跳过Modal确认，直接删除用于调试
    setIsDeleting(true);
    try {
      console.log('🗑️ Attempting to delete document with ID:', id);
      console.log('🌐 API base URL:', api.defaults.baseURL);
      console.log('🎯 Full delete URL will be:', `${api.defaults.baseURL}/document/${id}`);
      
      const response = await api.delete(`/document/${id}`);
      console.log('✅ Delete response:', response);
      console.log('✅ Delete response data:', response.data);
      
      message.success('文档删除成功');
      onDelete?.(id);
    } catch (error: any) {
      console.error('❌ 删除文档失败:', error);
      console.error('❌ 错误详情:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        fullError: error
      });
      
      let errorMessage = '删除文档失败';
      if (error.response?.data?.detail) {
        errorMessage = `删除失败: ${error.response.data.detail}`;
      } else if (error.response?.status === 404) {
        errorMessage = '文档不存在或已被删除';
      } else if (error.response?.status === 500) {
        errorMessage = '服务器内部错误';
      } else if (!error.response) {
        errorMessage = '网络连接错误';
      }
      
      message.error(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  // 处理预览操作
  const handlePreview = () => {
    onClick?.();
  };


  // 右下角操作菜单
  const menuItems = [
    {
      key: 'preview',
      label: '预览',
      icon: <EyeOutlined />
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true
    }
  ];

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    console.log('🎯 Menu clicked:', key);
    console.log('🎯 Available props:', { id, title, hasOnDelete: !!onDelete });
    
    if (key === 'preview') {
      console.log('👁️ Preview clicked');
      handlePreview();
    } else if (key === 'delete') {
      console.log('🗑️ Delete clicked, calling handleDelete...');
      handleDelete();
    }
  };

  const thumbnailElement = renderThumbnail();
  console.log('🔧 Final thumbnail element:', thumbnailElement);

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: '100%', overflow: 'visible' }}>
      <Card
        hoverable
        cover={
          <div 
            style={{ cursor: 'pointer' }}
            onClick={(e) => {
              console.log('🎯 Document thumbnail clicked, triggering preview');
              handlePreview();
            }}
          >
            {thumbnailElement}
          </div>
        }
        className={styles.documentCard}
        style={{
          boxShadow: isHighlighted 
            ? '0 0 0 2px #1890ff, 0 4px 12px rgba(24, 144, 255, 0.3)' 
            : '0 1px 3px rgba(0, 0, 0, 0.1)',
          opacity: isDeleting ? 0.6 : 1,
          border: isHighlighted ? '2px solid #1890ff' : undefined,
          backgroundColor: isHighlighted ? '#f6ffed' : undefined
        }}
        bodyStyle={{ 
          padding: '12px 16px',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}
      >
      <div>
        <h4 
          className={styles.documentTitle}
          style={{ cursor: 'pointer' }}
          onClick={(e) => {
            console.log('🎯 Document title clicked, triggering preview');
            handlePreview();
          }}
        >
          {title}
        </h4>
        <div className={styles.documentMeta}>
          {/* 分类标签 */}
          {categories && categories.length > 0 && (
            <div className={styles.documentCategories}>
              {categories.map((category) => {
                // 根据角色确定样式
                const isPrimary = category.role === 'primary_system';
                const isSecondary = category.role === 'secondary_system';
                const isUserRule = category.role === 'user_rule';
                
                // 确定图标和样式
                let icon = '🤖';
                let borderStyle = 'none';
                let opacity = 1;
                
                if (isUserRule) {
                  icon = '📁';
                  borderStyle = '1px dashed';
                } else if (isSecondary) {
                  icon = '🔗';
                  opacity = 0.8;
                } else if (isPrimary) {
                  icon = '⭐';
                }
                
                return (
                  <Tag 
                    key={category.id}
                    color={category.color}
                    style={{
                      fontSize: '10px',
                      padding: '0 4px',
                      margin: 0,
                      border: borderStyle,
                      opacity: opacity,
                      fontWeight: isPrimary ? 'bold' : 'normal'
                    }}
                    title={`${category.name} (${category.role}, 置信度: ${(category.confidence || 0) * 100}%)`}
                  >
                    {icon} {category.name}
                    {category.confidence && category.confidence < 1 && (
                      <span style={{ fontSize: '8px', opacity: 0.7 }}>
                        {Math.round(category.confidence * 100)}%
                      </span>
                    )}
                  </Tag>
                );
              })}
            </div>
          )}
          
          {/* 来源和时间 */}
          <div className={styles.documentFooter}>
            <Tag color={sourceTag.color}>{sourceTag.text}</Tag>
            <span style={{
              fontSize: '12px',
              color: '#999'
            }}>
              {formatDate(createdAt)}
            </span>
          </div>
        </div>
      </div>
      </Card>
      
      {/* 右上角操作按钮 */}
      <div 
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
        }}
      >
        <NativeDropdown
          items={menuItems}
          placement="bottomRight"
          onMenuClick={(key) => {
            handleMenuClick({ key });
          }}
          trigger={
            <div
              data-testid="document-more-button"
              className={styles.moreButton}
              style={{
                background: 'rgba(0, 0, 0, 0.6)',
                color: 'white',
                borderRadius: '4px',
                opacity: 0.8,
                padding: '4px 8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px',
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLElement).style.opacity = '1';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLElement).style.opacity = '0.8';
              }}
            >
              <MoreOutlined />
            </div>
          }
        />
      </div>
    </div>
  );
}

// 使用 memo 优化组件，避免不必要的重新渲染
export default memo(DocumentCard, (prevProps, nextProps) => {
  // 自定义比较函数，只有关键属性变化时才重新渲染
  return (
    prevProps.id === nextProps.id &&
    prevProps.title === nextProps.title &&
    prevProps.modality === nextProps.modality &&
    prevProps.sourceUri === nextProps.sourceUri &&
    prevProps.createdAt === nextProps.createdAt &&
    prevProps.isHighlighted === nextProps.isHighlighted &&
    JSON.stringify(prevProps.categories) === JSON.stringify(nextProps.categories)
  );
});