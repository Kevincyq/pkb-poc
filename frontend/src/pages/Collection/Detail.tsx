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
import PreviewContent from '../../components/PreviewContent';

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
        zIndex={2000}
        styles={{ 
          mask: { backgroundColor: 'rgba(0, 0, 0, 0.8)' }
        }}
      >
        {previewDocument && (
          <PreviewContent document={previewDocument} />
        )}
      </Modal>
    </MainLayout>
  );
}
