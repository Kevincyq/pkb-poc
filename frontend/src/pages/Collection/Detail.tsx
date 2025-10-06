import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Input, message, Empty, Spin, Modal, Tag } from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import MainLayout from '../../components/Layout/MainLayout';
import DocumentCard from '../../components/Document/DocumentCard';
import { getCategoryDocuments } from '../../services/collectionService';
import type { CollectionDocument } from '../../types/collection';
import styles from './Detail.module.css';
import { formatDateTime } from '../../utils/dateUtils';

const { Search } = Input;

export default function CollectionDetail() {
  const { categoryName } = useParams<{ categoryName: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [previewDocument, setPreviewDocument] = useState<CollectionDocument | null>(null);
  const [highlightContentId, setHighlightContentId] = useState<string | null>(null);

  // 处理URL中的highlight参数
  useEffect(() => {
    const highlight = searchParams.get('highlight');
    if (highlight) {
      setHighlightContentId(highlight);
      // 清除URL中的highlight参数，避免刷新时重复高亮
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete('highlight');
      navigate(`/collection/${categoryName}?${newSearchParams.toString()}`, { replace: true });
    }
  }, [searchParams, categoryName, navigate]);

  // 获取合集文档
  const { data, isLoading, error } = useQuery({
    queryKey: ['categoryDocuments', categoryName, searchQuery],
    queryFn: () => getCategoryDocuments(categoryName || '', searchQuery),
    enabled: !!categoryName,
  });

  // 当数据加载完成且有高亮文档时，滚动到该文档
  useEffect(() => {
    if (highlightContentId && data?.results && !isLoading) {
      const timer = setTimeout(() => {
        const highlightedElement = document.querySelector(`[data-content-id="${highlightContentId}"]`);
        if (highlightedElement) {
          highlightedElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
          });
          // 3秒后清除高亮
          setTimeout(() => {
            setHighlightContentId(null);
          }, 3000);
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [highlightContentId, data, isLoading]);

  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };

  const handleDocumentClick = (document: CollectionDocument) => {
    // 打开预览模态框
    setPreviewDocument(document);
  };

  const handleDocumentDelete = (deletedId: string) => {
    // 删除成功后，使用 React Query 刷新数据
    console.log('📋 Parent received delete notification for document ID:', deletedId);
    queryClient.invalidateQueries({
      queryKey: ['categoryDocuments', categoryName, searchQuery]
    });
    console.log('🔄 Query invalidated, data should refresh');
  };

  const handleClosePreview = () => {
    setPreviewDocument(null);
  };

  if (error) {
    message.error('加载文档列表失败');
  }

  return (
    <MainLayout>
      {/* 顶部导航区域 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          color: '#666'
        }}>
          <span 
            onClick={() => navigate('/')}
            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          >
            <HomeOutlined style={{ marginRight: '4px' }} />
            个人知识库助理
          </span>
          <span>/</span>
          <span style={{ color: '#333' }}>{categoryName}</span>
        </div>

        <Search
          placeholder="搜索文档..."
          allowClear
          onSearch={handleSearch}
          style={{ width: 250 }}
        />
      </div>

      {/* 文档卡片网格区域 */}
      <div className={styles.container}>
        {isLoading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '40px'
          }}>
            <Spin />
          </div>
        ) : data?.results.length ? (
          <div className={styles.documentGrid}>
            {data.results.map((document) => (
              <div key={document.content_id} data-content-id={document.content_id}>
                <DocumentCard
                  id={document.content_id}
                  title={document.title}
                  modality={document.modality as 'text' | 'image' | 'pdf'}
                  sourceUri={document.source_uri}
                  createdAt={document.created_at}
                  onClick={() => handleDocumentClick(document)}
                  onDelete={handleDocumentDelete}
                  isHighlighted={highlightContentId === document.content_id}
                />
              </div>
            ))}
          </div>
        ) : (
          <Empty
            style={{ padding: '40px' }}
            description={searchQuery ? "未找到相关文档" : "暂无文档"}
          />
        )}
      </div>

      {/* 预览模态框 */}
      <Modal
        title={previewDocument?.title}
        open={!!previewDocument}
        onCancel={handleClosePreview}
        footer={null}
        width={1200}
        centered
        style={{ top: 20 }}
      >
        {previewDocument && (
          <div style={{ textAlign: 'center' }}>
            {previewDocument.modality === 'image' ? (
              <div>
                <img
                  src={(() => {
                    // 获取API基础URL
                    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 
                      (window.location.hostname === 'localhost' 
                        ? 'http://localhost:8003/api' 
                        : 'https://pkb-test.kmchat.cloud/api'
                      );
                    // 从source_uri提取文件名
                    const fileName = previewDocument.source_uri.replace(/^(webui|nextcloud):\/\//, '');
                    // 使用原始文件API（而非缩略图）获取高清图片
                    return `${apiBaseUrl}/files/${encodeURIComponent(fileName)}`;
                  })()}
                  alt={previewDocument.title}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '70vh',
                    minHeight: '400px',
                    objectFit: 'contain',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                  }}
                  onError={(e) => {
                    // 如果原始图片加载失败，显示占位符
                    const target = e.target as HTMLImageElement;
                    target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7ml6Dms5Xmn6XnnIvlm77niYc8L3RleHQ+PC9zdmc+';
                  }}
                />
                <div style={{ marginTop: '16px', color: '#666' }}>
                  <p><strong>文件名：</strong>{previewDocument.title}</p>
                  <p><strong>来源：</strong>{previewDocument.source_uri.includes('webui://') ? 'WebUI上传' : '其他'}</p>
                  <p><strong>创建时间：</strong>{formatDateTime(previewDocument.created_at)}</p>
                  {previewDocument.category_name && (
                    <p><strong>分类：</strong>{previewDocument.category_name}</p>
                  )}
                  {previewDocument.tags && previewDocument.tags.length > 0 && (
                    <p>
                      <strong>标签：</strong>
                      {previewDocument.tags.map((tag: any, index: number) => (
                        <Tag key={index} color="blue" style={{ marginRight: '4px', marginTop: '4px' }}>
                          {tag.name}
                        </Tag>
                      ))}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div>
                <div style={{
                  padding: '40px',
                  background: '#f5f5f5',
                  borderRadius: '8px',
                  marginBottom: '16px'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
                  <p>文档预览功能开发中...</p>
                </div>
                <div style={{ color: '#666', textAlign: 'left' }}>
                  <p><strong>文件名：</strong>{previewDocument.title}</p>
                  <p><strong>类型：</strong>{previewDocument.modality}</p>
                  <p><strong>来源：</strong>{previewDocument.source_uri.includes('webui://') ? 'WebUI上传' : '其他'}</p>
                  <p><strong>创建时间：</strong>{formatDateTime(previewDocument.created_at)}</p>
                  {previewDocument.category_name && (
                    <p><strong>分类：</strong>{previewDocument.category_name}</p>
                  )}
                  {previewDocument.tags && previewDocument.tags.length > 0 && (
                    <p>
                      <strong>标签：</strong>
                      {previewDocument.tags.map((tag: any, index: number) => (
                        <Tag key={index} color="blue" style={{ marginRight: '4px', marginTop: '4px' }}>
                          {tag.name}
                        </Tag>
                      ))}
                    </p>
                  )}
                  {previewDocument.text && (
                    <div>
                      <p><strong>内容预览：</strong></p>
                      <div style={{
                        background: '#fafafa',
                        padding: '12px',
                        borderRadius: '4px',
                        maxHeight: '200px',
                        overflow: 'auto',
                        textAlign: 'left',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {previewDocument.text.substring(0, 500)}
                        {previewDocument.text.length > 500 && '...'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </MainLayout>
  );
}
