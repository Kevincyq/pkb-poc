import { useState } from 'react';
import { Row, Col, Button, message, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import MainLayout from '../../components/Layout/MainLayout';
import DocumentCard from '../../components/Document/DocumentCard';
import AIChat from '../../components/AIChat';
import Search from '../../components/Search';
import EmptyState from '../../components/EmptyState';
import { getCategoryDocuments } from '../../services/collectionService';
import type { CollectionDocument } from '../../types/collection';

export default function Collection() {
  const { categoryName } = useParams<{ categoryName: string }>();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState<string>('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['collection', categoryName, searchQuery],
    queryFn: () => getCategoryDocuments(categoryName || '', searchQuery),
    enabled: !!categoryName,
  });

  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };

  const handleDocumentClick = (document: CollectionDocument) => {
    console.log('Open document:', document);
  };

  const handleAddDocument = () => {
    console.log('Add new document to collection:', categoryName);
  };

  if (error) {
    message.error('加载合集数据失败');
  }

  return (
    <MainLayout>
      {/* 顶部导航栏 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '24px',
        padding: '0'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          color: '#666'
        }}>
          <span style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
            个人知识库助理
          </span>
          <span>/</span>
          <span style={{ color: '#333' }}>{categoryName}</span>
        </div>
        
        {/* 右侧操作区 */}
        <Space size={16}>
          <Search onSearch={handleSearch} />
          <Button 
            type="text" 
            icon={<PlusOutlined />}
            onClick={handleAddDocument}
            style={{ 
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0
            }}
          />
        </Space>
      </div>

      {/* 内容区域 */}
      <div style={{ width: '100%' }}>
        {isLoading ? (
          <EmptyState type="searching" />
        ) : (
          <>
            {searchQuery && (
              <div style={{ 
                marginBottom: '16px',
                fontSize: '14px',
                color: '#666'
              }}>
                为您搜索到以下内容
              </div>
            )}
            
            {data?.results && data.results.length > 0 ? (
              <>
                <div style={{ marginBottom: '16px', fontSize: '14px', color: '#666' }}>
                  显示 {data.results.length} 条内容 (API返回: {data.total || 'unknown'} 条)
                </div>
                <Row gutter={[16, 16]}>
                {data.results.map((document: CollectionDocument) => {
                  console.log('📋 Rendering document:', document.title, 'modality:', document.modality, 'sourceUri:', document.source_uri);
                  return (
                    <Col xs={24} sm={12} md={8} lg={6} xl={4} key={document.chunk_id || document.content_id}>
                      <DocumentCard
                        id={document.chunk_id || document.content_id}
                        title={document.title}
                        modality={document.modality}
                        sourceUri={document.source_uri}
                        createdAt={document.created_at}
                        onClick={() => handleDocumentClick(document)}
                      />
                    </Col>
                  );
                })}
              </Row>
              </>
            ) : (
              searchQuery ? (
                <div style={{ 
                  marginTop: '40px',
                  textAlign: 'center' 
                }}>
                  <EmptyState type="noResult" />
                </div>
              ) : (
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  height: '200px',
                  color: '#999'
                }}>
                  <p>该合集暂无文档</p>
                </div>
              )
            )}
          </>
        )}
      </div>

      {/* AI对话组件 */}
      <AIChat />
    </MainLayout>
  );
}