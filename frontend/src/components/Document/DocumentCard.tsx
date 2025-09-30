import { Card, Tag, Dropdown, Button, message } from 'antd';
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
import { useState } from 'react';
import api from '../../services/api';

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
  }>;
  onClick?: () => void;
  onDelete?: (id: string) => void;
  isHighlighted?: boolean; // 新增：是否高亮显示
}

export default function DocumentCard({
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
    
    // 如果是webui上传的图片，尝试使用后端缩略图
    if (sourceUri.includes('webui://')) {
      const fileName = sourceUri.replace('webui://', '');
      const thumbnailUrl = `//pkb.kmchat.cloud/api/files/thumbnail/${encodeURIComponent(fileName)}`;
      console.log(`📸 WebUI thumbnail URL: ${thumbnailUrl}`);
      return thumbnailUrl;
    }
    
    // 如果是nextcloud的图片，也可以尝试生成缩略图
    if (sourceUri.includes('nextcloud://')) {
      const fileName = sourceUri.replace('nextcloud://', '');
      const thumbnailUrl = `//pkb.kmchat.cloud/api/files/thumbnail/${encodeURIComponent(fileName)}`;
      console.log(`☁️ Nextcloud thumbnail URL: ${thumbnailUrl}`);
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
      
      if (thumbnailUrl) {
        return (
          <div style={{
            width: '100%',
            height: '180px', // 增加缩略图高度
            position: 'relative',
            backgroundColor: '#f5f5f5'
          }}>
            <img 
              src={thumbnailUrl} 
              alt={title} 
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
              onError={(e) => {
                console.log(`❌ Thumbnail failed to load: ${thumbnailUrl}`);
                console.log('Error event:', e);
                // 如果真实缩略图加载失败，显示彩色渐变回退
                const target = e.target as HTMLImageElement;
                const parent = target.parentElement;
                if (parent) {
                  const colorStyle = generateColorThumbnail(title, modality);
                  if (colorStyle) {
                    parent.innerHTML = '';
                    const fallbackDiv = document.createElement('div');
                    Object.assign(fallbackDiv.style, {
                      width: '100%',
                      height: '100%',
                      ...colorStyle
                    });
                    fallbackDiv.innerHTML = `
                      <div style="
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 8px;
                      ">
                        <div style="font-size: 48px;">🖼️</div>
                        <div style="
                          font-size: 12px;
                          text-align: center;
                          opacity: 0.9;
                          max-width: 120px;
                          overflow: hidden;
                          text-overflow: ellipsis;
                          white-space: nowrap;
                        ">${title}</div>
                      </div>
                    `;
                    parent.appendChild(fallbackDiv);
                  }
                }
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
            <div style={{
              width: '100%',
              height: '180px', // 增加缩略图高度
              position: 'relative',
              ...colorStyle
            }}>
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
      <div style={{
        width: '100%',
        height: '180px', // 统一缩略图高度
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${colorPair[0]}, ${colorPair[1]})`,
        flexDirection: 'column',
        gap: '12px'
      }}>
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

  // 格式化日期 - 始终显示完整日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    // 始终显示年/月/日格式
    return `${year}/${month}/${day}`;
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
    <div style={{ position: 'relative' }}>
      <Card 
        onClick={handlePreview}
        hoverable
        cover={thumbnailElement}
        style={{
          width: '100%',
          height: '300px', // 固定卡片总高度 (180px缩略图 + 120px内容区域)
          borderRadius: '8px',
          overflow: 'hidden',
          boxShadow: isHighlighted 
            ? '0 0 0 2px #1890ff, 0 4px 12px rgba(24, 144, 255, 0.3)' 
            : '0 1px 3px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.3s',
          opacity: isDeleting ? 0.6 : 1,
          display: 'flex',
          flexDirection: 'column',
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
        <h4 style={{
          fontSize: '14px',
          fontWeight: '500',
          color: '#333',
          margin: '0 0 8px 0',
          lineHeight: '1.3',
          height: '36px', // 固定标题区域高度 (14px * 1.3 * 2 ≈ 36px)
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {title}
        </h4>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {/* 分类标签 */}
          {categories && categories.length > 0 && (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '4px'
            }}>
              {categories.map((category) => (
                <Tag 
                  key={category.id}
                  color={category.color}
                  style={{
                    fontSize: '10px',
                    padding: '0 4px',
                    margin: 0,
                    border: category.is_system ? 'none' : '1px dashed'
                  }}
                >
                  {category.is_system ? '🤖' : '📁'} {category.name}
                </Tag>
              ))}
            </div>
          )}
          
          {/* 来源和时间 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
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
      <Dropdown
        menu={{ 
          items: menuItems,
          onClick: (info) => {
            console.log('🎯 Dropdown menu onClick triggered:', info);
            handleMenuClick(info);
          }
        }}
        placement="bottomRight"
        trigger={['click']}
        onOpenChange={(open) => {
          console.log('🎯 Dropdown open state changed:', open);
        }}
      >
        <Button
          type="text"
          icon={<MoreOutlined />}
          size="small"
          onClick={(e) => {
            console.log('🎯 More button clicked');
            e.stopPropagation();
          }}
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'rgba(0, 0, 0, 0.6)',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            zIndex: 10,
            opacity: 0.8,
            transition: 'opacity 0.3s'
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLElement).style.opacity = '1';
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLElement).style.opacity = '0.8';
          }}
        />
      </Dropdown>
    </div>
  );
}