import { useState, useEffect } from 'react';
import { Row, Col, Button, message, Upload, Modal, Input, Drawer } from 'antd';
import { SearchOutlined, PlusOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import MainLayout from '../../components/Layout/MainLayout';
import CollectionCard from '../../components/Collection/CollectionCard';
import AIInput from '../../components/AIInput/AIInput';
import UploadStatusCard, { type UploadFileStatus } from '../../components/Upload/UploadStatusCard';
import CreateCollectionModal from '../../components/Collection/CreateCollectionModal';
import type { UploadProps } from 'antd';
import * as collectionService from '../../services/collectionManageService';
import { uploadFile, getProcessingStatus } from '../../services/uploadService';
import api from '../../services/api';


interface Category {
  id: string;
  name: string;
  color: string;
  content_count: number;
}

// 使用服务中定义的类型
type CustomCollection = collectionService.CustomCollection;

export default function Home() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [categories, setCategories] = useState<Category[]>([]);
  const [customCollections, setCustomCollections] = useState<CustomCollection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renamingCollection, setRenamingCollection] = useState<CustomCollection | null>(null);
  const [newName, setNewName] = useState('');
  const [deletingCollection, setDeletingCollection] = useState<CustomCollection | null>(null);
  const [uploadFiles, setUploadFiles] = useState<UploadFileStatus[]>([]);
  const [uploadDrawerVisible, setUploadDrawerVisible] = useState(false);
  const [createCollectionModalVisible, setCreateCollectionModalVisible] = useState(false);
  const [processingBatch, setProcessingBatch] = useState<string | null>(null); // 防止重复批量上传

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // 并行加载智能合集和自建合集
      const [categoriesResponse, customCollectionsData] = await Promise.all([
        api.get('/search/categories/stats'),
        collectionService.getCustomCollections()
      ]);
      
      // 处理智能合集数据
      const categoriesData = categoriesResponse.data;
      
      if (categoriesData.categories && Array.isArray(categoriesData.categories)) {
        // 直接使用优化后的API返回的数据
        setCategories(categoriesData.categories);
      } else {
        throw new Error('Invalid data format');
      }
      
      // 处理自建合集数据
      setCustomCollections(customCollectionsData);
      
    } catch (err: any) {
      console.error('Failed to load data:', err);
      
      // 提供更友好的错误信息
      let errorMessage = '加载合集数据失败';
      if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errorMessage = '网络连接失败，请检查网络连接或稍后重试';
      } else if (err.response?.status === 404) {
        errorMessage = '服务暂时不可用，请稍后重试';
      } else if (err.message?.includes('CORS')) {
        errorMessage = '服务配置问题，请联系管理员';
      }
      
      setError(errorMessage);
      message.error(errorMessage);
      
      // 设置默认的空数据，避免页面完全无法使用
      setCategories([]);
      setCustomCollections([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 保持向后兼容
  const loadCategories = loadData;

  const handleSearch = () => {
    console.log('Search clicked');
  };

  const handleCreateCollection = () => {
    setCreateCollectionModalVisible(true);
  };

  const handleCreateCollectionSuccess = () => {
    setCreateCollectionModalVisible(false);
    loadData(); // 重新加载数据以显示新创建的合集
  };

  const handleDeleteCollection = (collectionId: string) => {
    console.log('Attempting to delete collection:', collectionId);
    const collection = customCollections.find(c => c.id === collectionId);
    if (collection) {
      setDeletingCollection(collection);
    }
  };

  const confirmDelete = async () => {
    if (!deletingCollection) return;
    
    try {
      console.log('Calling delete API for collection:', deletingCollection.id);
      await collectionService.deleteCollection(deletingCollection.id);
      console.log('Delete API call successful, updating UI...');
      
      setCustomCollections(collections => 
        collections.filter(c => c.id !== deletingCollection.id)
      );
      
      setDeletingCollection(null);
      message.success('合集删除成功');
    } catch (error: any) {
      console.error('Failed to delete collection:', error);
      message.error(`删除合集失败: ${error.message || '未知错误'}`);
    }
  };

  const cancelDelete = () => {
    console.log('User cancelled delete operation');
    setDeletingCollection(null);
  };

  const handleRenameCollection = (collection: CustomCollection) => {
    setRenamingCollection(collection);
    setNewName(collection.name);
  };

  const handleRenameConfirm = async () => {
    if (renamingCollection && newName.trim()) {
      try {
        const updatedCollection = await collectionService.updateCollection(
          renamingCollection.id, 
          { name: newName.trim() }
        );
        
        setCustomCollections(collections =>
          collections.map(c =>
            c.id === renamingCollection.id ? updatedCollection : c
          )
        );
        
        setRenamingCollection(null);
        setNewName('');
        message.success('合集重命名成功');
      } catch (error: any) {
        console.error('Failed to rename collection:', error);
        message.error(`重命名失败: ${error.message || '未知错误'}`);
      }
    }
  };

  const handleAIInput = (value: string) => {
    console.log('AI Input:', value);
  };

  const handleCollectionClick = (_categoryId: string, categoryName: string) => {
    // 清除相关的查询缓存，确保显示最新数据
    queryClient.invalidateQueries({ 
      queryKey: ['categoryDocuments', categoryName] 
    });
    navigate(`/collection/${encodeURIComponent(categoryName)}`);
  };

  // 处理多文件上传
  const handleMultipleFileUpload = async (fileList: File[]): Promise<void> => {
    console.log(`开始批量上传 ${fileList.length} 个文件`);
    
    // 显示上传抽屉
    setUploadDrawerVisible(true);
    
    // 简化逻辑：直接并发上传所有文件，但限制并发数
    const concurrentLimit = 3; // 降低并发数，避免服务器压力
    
    // 分批处理文件
    for (let i = 0; i < fileList.length; i += concurrentLimit) {
      const batch = fileList.slice(i, i + concurrentLimit);
      
      // 并发处理当前批次
      const batchPromises = batch.map(async (file) => {
        try {
          console.log(`开始上传文件: ${file.name}`);
          await handleFileUpload(file);
          console.log(`文件上传完成: ${file.name}`);
        } catch (error) {
          console.error(`文件 ${file.name} 上传失败:`, error);
        }
      });
      
      // 等待当前批次完成再处理下一批次
      await Promise.all(batchPromises);
      console.log(`批次 ${Math.floor(i / concurrentLimit) + 1} 完成`);
    }
    
    console.log('所有文件上传完成');
  };

  // 处理文件上传
  const handleFileUpload = async (file: File) => {
    const fileId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // 创建上传文件状态
    const uploadFileStatus: UploadFileStatus = {
      id: fileId,
      fileName: file.name,
      fileSize: file.size,
      status: 'uploading',
      progress: 0,
      uploadProgress: 0,
      startTime: Date.now()
    };
    
    // 添加到上传列表并显示抽屉
    setUploadFiles(prev => [...prev, uploadFileStatus]);
    setUploadDrawerVisible(true);
    
    try {
      // 使用统一的上传服务
      const result = await uploadFile(file);

      if (result.status === 'success') {
        // 更新状态为解析中
        setUploadFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'parsing', 
            progress: 30,
            contentId: result.content_id 
          } : f
        ));
        
        // 开始轮询处理状态
        pollProcessingStatus(result.content_id, fileId);
      } else {
        throw new Error(result.message || '上传失败');
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      
      // 更新状态为错误
      setUploadFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          status: 'error', 
          errorMessage: error.message 
        } : f
      ));
    }
  };

  // 轮询处理状态
  const pollProcessingStatus = (contentId: string, fileId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        // 使用统一的状态查询服务
        const statusData = await getProcessingStatus(contentId);
        
        // 更新文件状态
        setUploadFiles(prev => prev.map(f => {
          if (f.id === fileId) {
            console.log(`🔄 Updating file status for ${fileId}:`, {
              classification_status: statusData.classification_status,
              show_classification: statusData.show_classification,
              categories: statusData.categories
            });
            
            // 根据classification_status和show_classification来判断状态
            if (statusData.classification_status === 'completed' && statusData.show_classification) {
              // 分类完成，显示结果
              const categories = statusData.categories?.map((cat: any) => ({
                id: cat.id,
                name: cat.name,
                confidence: cat.confidence || 0.8
              })) || [];
              
              console.log(`✅ File ${fileId} classification completed with categories:`, categories);
              
              return {
                ...f,
                status: 'completed',
                progress: 100,
                categories
              };
            } else if (statusData.classification_status === 'pending' || !statusData.show_classification) {
              // 分类中
              const progress = statusData.classification_status === 'quick_done' ? 50 : 
                              statusData.classification_status === 'ai_done' ? 80 : 30;
              
              console.log(`⏳ File ${fileId} still classifying, progress: ${progress}%`);
              
              return {
                ...f,
                status: 'classifying',
                progress
              };
            } else {
              // 其他状态，保持当前状态
              console.log(`🤔 File ${fileId} unknown status, keeping current state`);
              return f;
            }
          }
          return f;
        }));
        
        // 检查是否应该停止轮询
        if (statusData.classification_status === 'completed' && statusData.show_classification) {
          console.log(`🛑 Stopping polling for ${fileId} - classification completed`);
          clearInterval(pollInterval);
          
          // 刷新页面数据
          loadCategories();
        } else {
          console.log(`🔄 Continuing polling for ${fileId} - status: ${statusData.classification_status}, show: ${statusData.show_classification}`);
        }
      } catch (error) {
        console.error('Status polling error:', error);
        clearInterval(pollInterval);
        
        // 更新为错误状态
        setUploadFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'error', 
            errorMessage: '状态查询失败' 
          } : f
        ));
      }
    }, 1500); // 每1.5秒轮询一次，减少服务器压力

    // 20秒后停止轮询（减少无效轮询）
    setTimeout(() => {
      clearInterval(pollInterval);
      
      // 如果还没完成，标记为超时
      setUploadFiles(prev => prev.map(f => 
        f.id === fileId && f.status === 'classifying' ? { 
          ...f, 
          status: 'error', 
          errorMessage: '分类超时，请刷新页面查看结果' 
        } : f
      ));
    }, 20000);
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,  // 启用多文件选择
    showUploadList: false,
    beforeUpload: (file, fileList) => {
      // 处理多文件上传
      if (fileList && fileList.length > 1) {
        // 生成批次ID，防止重复处理
        const batchId = fileList.map(f => f.name).sort().join('|');
        
        // 检查是否已经在处理这个批次
        if (processingBatch !== batchId) {
          setProcessingBatch(batchId);
          console.log(`开始处理批次: ${batchId}, 文件数量: ${fileList.length}`);
          
          // 批量处理多个文件
          handleMultipleFileUpload(fileList).finally(() => {
            // 处理完成后清除批次标记
            setTimeout(() => setProcessingBatch(null), 1000);
          });
        } else {
          console.log(`批次 ${batchId} 已在处理中，跳过重复调用`);
        }
      } else {
        // 单文件处理
        handleFileUpload(file);
      }
      return false; // 阻止默认上传行为
    },
    accept: '.txt,.md,.pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp,.doc,.docx,.ppt,.pptx,.xls,.xlsx',
  };

  // 对合集进行排序
  const sortedCategories = categories.sort((a, b) => {
    const order = ['职场商务', '科技前沿', '学习成长', '生活点滴'];
    return order.indexOf(a.name) - order.indexOf(b.name);
  });

  // 对自建合集按创建时间倒序排序
  const sortedCustomCollections = [...customCollections].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <MainLayout>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '32px'
      }}>
        <h1 style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: '500',
          color: '#1f1f1f',
          lineHeight: '28px'
        }}>
          个人知识库助理
        </h1>
        <div style={{
          display: 'flex',
          gap: '16px'
        }}>
          <Button
            type="text"
            icon={<SearchOutlined style={{ fontSize: '18px' }} />}
            onClick={handleSearch}
            style={{
              width: '32px',
              height: '32px',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          />
          {uploadFiles.length > 0 && (
            <Button
              type="text"
              icon={<FileTextOutlined style={{ fontSize: '18px' }} />}
              onClick={() => setUploadDrawerVisible(true)}
              style={{
                width: '32px',
                height: '32px',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative'
              }}
            >
              {uploadFiles.filter(f => f.status !== 'completed').length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: -2,
                  right: -2,
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: '#ff4d4f',
                  border: '1px solid #fff'
                }} />
              )}
            </Button>
          )}
          <Upload {...uploadProps}>
            <Button
              type="text"
              icon={<PlusOutlined style={{ fontSize: '18px' }} />}
              style={{
                width: '32px',
                height: '32px',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            />
          </Upload>
        </div>
      </div>

      <div style={{ padding: '0 0 120px' }}>
        {isLoading ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 0',
            color: '#666' 
          }}>
            加载中...
          </div>
        ) : error ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 0',
            color: '#ff4d4f' 
          }}>
            加载失败，请刷新重试
          </div>
        ) : (
          <Row gutter={[16, 16]}>
            {/* Create Card */}
            <Col span={4}>
              <CollectionCard
                title=""
                contentCount={0}
                isCreateCard
                onClick={handleCreateCollection}
              />
            </Col>
            
            {/* Custom Collections */}
            {sortedCustomCollections.map(collection => {
              console.log('Rendering collection:', collection.id, collection.name);
              return (
                <Col span={4} key={collection.id}>
                  <CollectionCard
                    title={collection.name}
                    contentCount={collection.content_count}
                    isCustomCollection
                    onDelete={() => {
                      console.log('Delete button clicked for collection:', collection.id, typeof collection.id);
                      handleDeleteCollection(collection.id);
                    }}
                    onRename={() => handleRenameCollection(collection)}
                    onClick={() => handleCollectionClick(collection.id, collection.name)}
                  />
                </Col>
              );
            })}
            
            {/* System Categories */}
            {sortedCategories.map(category => (
              <Col span={4} key={category.id}>
                <CollectionCard
                  title={category.name}
                  contentCount={category.content_count}
                  onClick={() => handleCollectionClick(category.id, category.name)}
                />
              </Col>
            ))}
          </Row>
        )}
      </div>

      <AIInput onSend={handleAIInput} />

      {/* 重命名对话框 */}
      <Modal
        title="重命名合集"
        open={!!renamingCollection}
        onOk={handleRenameConfirm}
        onCancel={() => setRenamingCollection(null)}
      >
        <Input
          value={newName}
          onChange={e => setNewName(e.target.value)}
          placeholder="请输入新的合集名称"
        />
      </Modal>

      {/* 删除确认对话框 */}
      <Modal
        title="确认删除"
        open={!!deletingCollection}
        onOk={confirmDelete}
        onCancel={cancelDelete}
        okText="确定删除"
        cancelText="取消"
        okType="danger"
      >
        <p>确定要删除合集 <strong>"{deletingCollection?.name}"</strong> 吗？</p>
        <p>删除后合集中的文档将移除分类，但文档本身不会被删除。</p>
      </Modal>

      {/* 文件上传状态抽屉 */}
      <Drawer
        title={(
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileTextOutlined />
            <span>文件上传状态</span>
            {uploadFiles.filter(f => f.status !== 'completed').length > 0 && (
              <span style={{ 
                fontSize: 12, 
                color: '#666',
                backgroundColor: '#f0f0f0',
                padding: '2px 6px',
                borderRadius: 10
              }}>
                {uploadFiles.filter(f => f.status !== 'completed').length} 个处理中
              </span>
            )}
          </div>
        )}
        placement="right"
        width={400}
        open={uploadDrawerVisible}
        onClose={() => setUploadDrawerVisible(false)}
        extra={
          uploadFiles.length > 0 && (
            <Button 
              size="small" 
              onClick={() => {
                setUploadFiles(prev => prev.filter(f => f.status !== 'completed'));
                if (uploadFiles.filter(f => f.status !== 'completed').length === 0) {
                  setUploadDrawerVisible(false);
                }
              }}
            >
              清除已完成
            </Button>
          )
        }
      >
        {uploadFiles.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 0',
            color: '#999' 
          }}>
            暂无上传文件
          </div>
        ) : (
          <div>
            {uploadFiles.map(file => (
              <UploadStatusCard
                key={file.id}
                file={file}
                onViewCollection={(categoryName) => {
                  setUploadDrawerVisible(false);
                  // 清除相关的查询缓存，确保显示最新数据
                  queryClient.invalidateQueries({ 
                    queryKey: ['categoryDocuments', categoryName] 
                  });
                  navigate(`/collection/${encodeURIComponent(categoryName)}`);
                }}
                onRetry={(fileId) => {
                  // TODO: 实现重试逻辑
                  console.log('Retry file:', fileId);
                }}
                onRemove={(fileId) => {
                  setUploadFiles(prev => prev.filter(f => f.id !== fileId));
                }}
              />
            ))}
          </div>
        )}
      </Drawer>

      {/* 创建合集模态框 */}
      <CreateCollectionModal
        open={createCollectionModalVisible}
        onCancel={() => setCreateCollectionModalVisible(false)}
        onSuccess={handleCreateCollectionSuccess}
      />
    </MainLayout>
  );
}