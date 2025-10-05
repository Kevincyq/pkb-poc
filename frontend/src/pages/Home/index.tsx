import { useState, useEffect } from 'react';
import { Row, Col, Button, message, Upload, Modal, Input, Drawer, Select, Slider, Tag, Progress, Tooltip } from 'antd';
import { SearchOutlined, PlusOutlined, FileTextOutlined, FilterOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import MainLayout from '../../components/Layout/MainLayout';
import CollectionCard from '../../components/Collection/CollectionCard';
import AIInput from '../../components/AIInput/AIInput';
import UploadStatusCard, { type UploadFileStatus } from '../../components/Upload/UploadStatusCard';
import CreateCollectionModal from '../../components/Collection/CreateCollectionModal';
import SearchOverlay from '../../components/SearchOverlay';
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
  
  // 批次状态管理
  interface BatchStats {
    total: number;
    completed: number;
    failed: number;
    processing: number;
    overallProgress: number;
  }
  
  const getBatchStats = (): BatchStats => {
    const total = uploadFiles.length;
    const completed = uploadFiles.filter(f => f.status === 'completed').length;
    const failed = uploadFiles.filter(f => f.status === 'error').length;
    const processing = uploadFiles.filter(f => ['uploading', 'parsing', 'classifying'].includes(f.status)).length;
    
    // 计算整体进度
    const totalProgress = uploadFiles.reduce((sum, file) => sum + (file.progress || 0), 0);
    const overallProgress = total > 0 ? Math.round(totalProgress / total) : 0;
    
    return { total, completed, failed, processing, overallProgress };
  };
  
  // 搜索相关状态
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [searchOverlayVisible, setSearchOverlayVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchFilters, setSearchFilters] = useState({
    categories: [] as string[],
    collections: [] as string[],
    modality: undefined as string | undefined,
    role: undefined as string | undefined,
    source: undefined as string | undefined,
    confidence: [0, 1] as [number, number]
  });

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
    setSearchOverlayVisible(true);
  };

  const performSearch = async () => {
    const trimmedQuery = searchQuery.trim();
    if (!trimmedQuery) {
      message.warning('请输入搜索关键词');
      return;
    }

    // 验证搜索查询长度
    if (trimmedQuery.length > 200) {
      message.warning('搜索关键词过长，请缩短后重试');
      return;
    }

    setSearchLoading(true);
    try {
      // 构建搜索参数
      const params = new URLSearchParams();
      params.append('q', trimmedQuery);
      params.append('top_k', '20');
      params.append('search_type', 'hybrid');

      // 添加过滤条件
      if (searchFilters.categories.length > 0) {
        params.append('categories', searchFilters.categories.join(','));
      }
      if (searchFilters.collections.length > 0) {
        params.append('collections', searchFilters.collections.join(','));
      }
      if (searchFilters.modality) {
        params.append('modality', searchFilters.modality);
      }
      if (searchFilters.role) {
        params.append('role', searchFilters.role);
      }
      if (searchFilters.source) {
        params.append('source', searchFilters.source);
      }
      if (searchFilters.confidence[0] > 0) {
        params.append('confidence_min', searchFilters.confidence[0].toString());
      }
      if (searchFilters.confidence[1] < 1) {
        params.append('confidence_max', searchFilters.confidence[1].toString());
      }

      const response = await api.get(`/search?${params.toString()}`);
      
      // 验证响应数据
      if (!response.data) {
        throw new Error('搜索响应数据为空');
      }
      
      const results = response.data.results || [];
      setSearchResults(results);
      
      if (results.length === 0) {
        message.info('没有找到相关内容，请尝试使用不同的关键词或调整过滤条件');
      } else {
        console.log(`🔍 Search completed: found ${results.length} results`);
      }
    } catch (error: any) {
      console.error('Search error:', error);
      
      // 更详细的错误处理
      if (error.response?.status === 400) {
        message.error('搜索参数有误，请检查输入');
      } else if (error.response?.status === 500) {
        message.error('服务器错误，请稍后重试');
      } else if (error.code === 'NETWORK_ERROR') {
        message.error('网络连接失败，请检查网络');
      } else {
        message.error('搜索失败，请重试');
      }
    } finally {
      setSearchLoading(false);
    }
  };

  const resetSearchFilters = () => {
    setSearchFilters({
      categories: [],
      collections: [],
      modality: undefined,
      role: undefined,
      source: undefined,
      confidence: [0, 1]
    });
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

  // 处理多文件上传 - 重构版本
  const handleMultipleFileUpload = async (fileList: File[], batchId: string): Promise<void> => {
    console.log(`🚀 开始批量上传 ${fileList.length} 个文件，批次ID: ${batchId}`);
    
    // 智能并发控制：根据文件大小决定并发数
    const getOptimalConcurrency = (files: File[]): number => {
      const totalSize = files.reduce((sum, file) => sum + (file.size || 0), 0);
      const avgSize = totalSize / files.length;
      
      // 根据平均文件大小调整并发数
      if (avgSize < 1024 * 1024) {        // < 1MB: 高并发
        return Math.min(5, files.length);
      } else if (avgSize < 10 * 1024 * 1024) {  // 1-10MB: 中并发
        return Math.min(3, files.length);
      } else {                             // > 10MB: 低并发
        return Math.min(2, files.length);
      }
    };
    
    const concurrentLimit = getOptimalConcurrency(fileList);
    console.log(`📊 智能并发控制：${concurrentLimit} 个并发，平均文件大小: ${(fileList.reduce((sum, f) => sum + (f.size || 0), 0) / fileList.length / 1024 / 1024).toFixed(1)}MB`);
    
    let completedCount = 0;
    let failedCount = 0;
    
    // 分批处理文件，确保稳定性
    for (let i = 0; i < fileList.length; i += concurrentLimit) {
      const batch = fileList.slice(i, i + concurrentLimit);
      console.log(`📦 处理批次 ${Math.floor(i / concurrentLimit) + 1}/${Math.ceil(fileList.length / concurrentLimit)}: ${batch.length} 个文件`);
      
      // 并发处理当前批次
      const batchPromises = batch.map(async (file, index) => {
        const globalIndex = i + index;
        try {
          console.log(`⬆️  [${globalIndex + 1}/${fileList.length}] 开始上传: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`);
          await handleFileUpload(file);
          completedCount++;
          console.log(`✅ [${globalIndex + 1}/${fileList.length}] 上传完成: ${file.name}`);
        } catch (error) {
          failedCount++;
          console.error(`❌ [${globalIndex + 1}/${fileList.length}] 上传失败: ${file.name}`, error);
          
          // 确保失败的文件也有状态显示
          const fileId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          setUploadFiles(prev => {
            // 检查是否已经存在这个文件的记录
            const existingFile = prev.find(f => f.fileName === file.name && f.status === 'uploading');
            if (!existingFile) {
              // 如果不存在，添加一个失败状态的记录
              const failedFileStatus: UploadFileStatus = {
                id: fileId,
                fileName: file.name,
                fileSize: file.size,
                status: 'error',
                progress: 0,
                errorMessage: error instanceof Error ? error.message : '上传失败',
                startTime: Date.now()
              };
              return [...prev, failedFileStatus];
            }
            return prev;
          });
        }
      });
      
      // 等待当前批次完成
      await Promise.all(batchPromises);
      
      // 批次间短暂延迟，避免服务器压力过大
      if (i + concurrentLimit < fileList.length) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }
    
    console.log(`🎉 批量上传完成！成功: ${completedCount}, 失败: ${failedCount}, 总计: ${fileList.length}`);
    
    // 显示完成提示
    if (failedCount === 0) {
      message.success(`批量上传完成！成功上传 ${completedCount} 个文件`);
    } else if (completedCount > 0) {
      message.warning(`批量上传完成！成功 ${completedCount} 个，失败 ${failedCount} 个`);
    } else {
      message.error(`批量上传失败！${failedCount} 个文件上传失败`);
    }
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
      // 使用统一的上传服务，添加进度回调
      const result = await uploadFile(file, (progressEvent) => {
        // 实时更新上传进度
        setUploadFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            uploadProgress: progressEvent.progress,
            progress: Math.min(progressEvent.progress * 0.3, 30) // 上传占总进度的30%
          } : f
        ));
      });

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

  // 轮询处理状态 - 智能轮询版本
  const pollProcessingStatus = (contentId: string, fileId: string) => {
    let pollCount = 0;
    
    // 获取文件信息以调整轮询策略
    const fileInfo = uploadFiles.find(f => f.id === fileId);
    const isImage = fileInfo?.fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i);
    const isLargeFile = (fileInfo?.fileSize || 0) > 10 * 1024 * 1024; // 10MB
    
    // 智能轮询参数
    const getPollingConfig = () => {
      if (isImage) {
        return { maxPolls: 20, interval: 1000 }; // 图片：20秒，1秒间隔
      } else if (isLargeFile) {
        return { maxPolls: 60, interval: 2000 }; // 大文件：2分钟，2秒间隔
      } else {
        return { maxPolls: 40, interval: 1500 }; // 普通文件：1分钟，1.5秒间隔
      }
    };
    
    const { maxPolls, interval } = getPollingConfig();
    console.log(`🔄 Starting smart polling for ${fileId}: maxPolls=${maxPolls}, interval=${interval}ms, isImage=${isImage}, isLarge=${isLargeFile}`);
    
    const pollInterval = setInterval(async () => {
      pollCount++;
      
      try {
        // 使用统一的状态查询服务
        const statusData = await getProcessingStatus(contentId);
        
        // 更新文件状态
        setUploadFiles(prev => prev.map(f => {
          if (f.id === fileId) {
            console.log(`🔄 [${pollCount}/${maxPolls}] Updating file status for ${fileId}:`, {
              processing_status: statusData.processing_status,
              parsing_status: (statusData as any).parsing_status,
              classification_status: statusData.classification_status,
              show_classification: statusData.show_classification,
              categories_count: statusData.categories?.length || 0
            });
            
            // 智能状态判断逻辑
            if (statusData.classification_status === 'completed' && statusData.show_classification) {
              // 分类完成，显示结果
              const categories = statusData.categories?.map((cat: any) => ({
                id: cat.id,
                name: cat.name,
                confidence: cat.confidence || 0.8,
                role: cat.role || 'primary_system',
                source: cat.source || 'ml',
                color: cat.role === 'primary_system' ? 'blue' : 
                       cat.role === 'secondary_system' ? 'cyan' : 
                       cat.role === 'user_rule' ? 'green' : 'default',
                is_system: cat.source === 'ml' || cat.source === 'heuristic'
              })) || [];
              
              console.log(`✅ File ${fileId} classification completed with ${categories.length} categories`);
              
              return {
                ...f,
                status: 'completed',
                progress: 100,
                categories
              };
            } else {
              // 根据详细状态显示进度和状态
              let progress = 30;
              let status: 'uploading' | 'parsing' | 'classifying' = 'parsing';
              
              // 根据解析状态
              const parsingStatus = (statusData as any).parsing_status;
              if (parsingStatus === 'parsing') {
                progress = 35;
                status = 'parsing';
              } else if (parsingStatus === 'completed') {
                progress = 50;
                status = 'classifying';
                
                // 根据分类状态细化进度
                if ((statusData.classification_status as any) === 'quick_processing') {
                  progress = 60;
                } else if (statusData.classification_status === 'quick_done') {
                  progress = 70;
                } else if ((statusData.classification_status as any) === 'ai_processing') {
                  progress = 85;
                }
              }
              
              console.log(`⏳ File ${fileId} processing: parsing=${parsingStatus}, classification=${statusData.classification_status}, progress=${progress}%`);
              
              return {
                ...f,
                status,
                progress
              };
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
        } else if (pollCount >= maxPolls) {
          // 达到最大轮询次数，但不标记为失败
          console.log(`⏰ Polling timeout for ${fileId}, but file may still be processing`);
          clearInterval(pollInterval);
          
          setUploadFiles(prev => prev.map(f => 
            f.id === fileId && f.status !== 'completed' ? { 
              ...f, 
              status: 'classifying',
              progress: 95,
              errorMessage: '处理中，请稍候或刷新页面查看结果' 
            } : f
          ));
        }
      } catch (error) {
        console.error(`❌ Status polling error for ${fileId}:`, error);
        
        // 网络错误不立即停止轮询，给几次重试机会
        if (pollCount < 5) {
          console.log(`🔄 Retrying status check for ${fileId} (attempt ${pollCount})`);
          return; // 继续轮询
        }
        
        clearInterval(pollInterval);
        
        // 更新为错误状态
        setUploadFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'error', 
            errorMessage: '状态查询失败，请刷新页面查看结果' 
          } : f
        ));
      }
    }, interval); // 使用智能间隔
  };

  // 重试文件上传/处理
  const handleRetryFile = async (fileId: string) => {
    const fileToRetry = uploadFiles.find(f => f.id === fileId);
    if (!fileToRetry) {
      message.error('找不到要重试的文件');
      return;
    }

    console.log(`🔄 Retrying file: ${fileToRetry.fileName}`);

    // 检查错误类型，决定重试策略
    const errorMessage = fileToRetry.errorMessage || '';
    
    if (errorMessage.includes('网络') || errorMessage.includes('连接') || errorMessage.includes('超时')) {
      // 网络错误：重新上传
      message.info(`正在重新上传文件: ${fileToRetry.fileName}`);
      
      // 重置文件状态
      setUploadFiles(prev => prev.map(f => 
        f.id === fileId ? {
          ...f,
          status: 'uploading',
          progress: 0,
          uploadProgress: 0,
          errorMessage: undefined,
          startTime: Date.now()
        } : f
      ));

      // 需要重新获取File对象，这里暂时提示用户重新选择
      message.warning('网络错误导致的失败需要重新选择文件上传');
      
    } else if (errorMessage.includes('状态查询') || errorMessage.includes('处理中')) {
      // 状态查询错误：重新轮询
      message.info(`正在重新检查文件状态: ${fileToRetry.fileName}`);
      
      if (fileToRetry.contentId) {
        // 重置状态并重新开始轮询
        setUploadFiles(prev => prev.map(f => 
          f.id === fileId ? {
            ...f,
            status: 'classifying',
            progress: 30,
            errorMessage: undefined
          } : f
        ));
        
        // 重新开始轮询
        pollProcessingStatus(fileToRetry.contentId, fileId);
      } else {
        message.error('缺少内容ID，无法重新检查状态');
      }
      
    } else {
      // 其他错误：提示用户重新上传
      message.warning('该文件处理失败，建议重新选择文件上传');
    }
  };

  // 批量重试失败文件
  const handleBatchRetry = () => {
    const failedFiles = uploadFiles.filter(f => f.status === 'error');
    
    if (failedFiles.length === 0) {
      message.info('没有失败的文件需要重试');
      return;
    }

    console.log(`🔄 Batch retrying ${failedFiles.length} failed files`);
    
    // 分类错误类型
    const networkErrors = failedFiles.filter(f => 
      (f.errorMessage || '').includes('网络') || 
      (f.errorMessage || '').includes('连接') ||
      (f.errorMessage || '').includes('超时')
    );
    
    const statusErrors = failedFiles.filter(f => 
      (f.errorMessage || '').includes('状态查询') || 
      (f.errorMessage || '').includes('处理中')
    );

    // 重试状态查询错误
    if (statusErrors.length > 0) {
      message.info(`正在重新检查 ${statusErrors.length} 个文件的状态`);
      
      statusErrors.forEach(file => {
        if (file.contentId) {
          setUploadFiles(prev => prev.map(f => 
            f.id === file.id ? {
              ...f,
              status: 'classifying',
              progress: 30,
              errorMessage: undefined
            } : f
          ));
          
          pollProcessingStatus(file.contentId, file.id);
        }
      });
    }

    // 网络错误需要重新上传
    if (networkErrors.length > 0) {
      message.warning(`${networkErrors.length} 个文件因网络错误失败，需要重新选择文件上传`);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,  // 启用多文件选择
    showUploadList: false,
    beforeUpload: (file, fileList) => {
      // 关键修复：只在处理第一个文件时触发批次处理
      const isFirstFile = fileList && fileList.indexOf(file) === 0;
      
      if (fileList && fileList.length > 1) {
        // 🔥 MVP限制：更保守的文件限制
        if (isFirstFile) {
          // 验证文件数量（MVP：最多5个文件）
          if (fileList.length > 5) {
            message.error(`MVP阶段一次最多只能上传5个文件，当前选择了${fileList.length}个文件`);
            return false;
          }
          
          // 验证单个文件大小（MVP：每个文件最大20MB）
          const maxSingleSize = 20 * 1024 * 1024; // 20MB
          const oversizedFiles = fileList.filter(f => (f.size || 0) > maxSingleSize);
          if (oversizedFiles.length > 0) {
            message.error(`MVP阶段单个文件不能超过20MB，以下文件超限：${oversizedFiles.map(f => `${f.name}(${(f.size / 1024 / 1024).toFixed(1)}MB)`).join(', ')}`);
            return false;
          }
          
          // 验证总文件大小（保守估计：5个文件×20MB = 100MB）
          const totalSize = fileList.reduce((sum, f) => sum + (f.size || 0), 0);
          const maxTotalSize = 100 * 1024 * 1024; // 100MB
          if (totalSize > maxTotalSize) {
            message.error(`批量上传总大小不能超过100MB，当前：${(totalSize / 1024 / 1024).toFixed(1)}MB`);
            return false;
          }
          
          const batchId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          console.log(`开始批次上传: ${batchId}, 文件数量: ${fileList.length}, 总大小: ${(totalSize / 1024 / 1024).toFixed(1)}MB`);
          
          // 显示上传抽屉
          setUploadDrawerVisible(true);
          
          // 立即处理整个批次
          handleMultipleFileUpload(fileList, batchId);
        }
        // 其他文件直接返回false，不做处理
      } else {
        // 🔥 MVP限制：单文件上传验证
        const maxSingleSize = 20 * 1024 * 1024; // 20MB
        if ((file.size || 0) > maxSingleSize) {
          message.error(`MVP阶段单个文件不能超过20MB，当前文件 ${file.name} 大小为 ${(file.size / 1024 / 1024).toFixed(1)}MB`);
          return false;
        }
        
        // 单文件处理
        console.log(`开始单文件上传: ${file.name}`);
        handleFileUpload(file);
      }
      return false; // 阻止默认上传行为
    },
    accept: '.txt,.md,.pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp',  // ⚠️ Office文档暂不支持
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
          <Tooltip 
            title={
              <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '4px', color: '#1890ff' }}>📁 文件上传限制 (MVP版本)</div>
                <div style={{ marginBottom: '2px' }}>✅ 支持格式：.txt, .md, .pdf</div>
                <div style={{ marginBottom: '2px' }}>✅ 支持图片：.jpg, .jpeg, .png, .gif, .bmp, .webp</div>
                <div style={{ marginBottom: '2px' }}>❌ 暂不支持：Office文档(.doc, .xls, .ppt等)</div>
                <div style={{ marginBottom: '2px' }}>📏 单文件大小：≤ 20MB</div>
                <div style={{ marginBottom: '2px' }}>📦 批量上传：≤ 5个文件</div>
                <div style={{ color: '#52c41a' }}>💡 小文件处理更快，体验更佳</div>
              </div>
            }
            placement="bottomRight"
            overlayStyle={{ maxWidth: '280px' }}
          >
            <Button
              type="text"
              icon={<InfoCircleOutlined style={{ fontSize: '16px', color: '#1890ff' }} />}
              style={{
                width: '24px',
                height: '24px',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginLeft: '4px'
              }}
            />
          </Tooltip>
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
            {(() => {
              const stats = getBatchStats();
              if (stats.total > 0) {
                return (
                  <span style={{ 
                    fontSize: 12, 
                    color: '#666',
                    backgroundColor: '#f0f0f0',
                    padding: '2px 6px',
                    borderRadius: 10
                  }}>
                    {stats.processing > 0 ? `${stats.processing} 个处理中` : 
                     stats.failed > 0 ? `${stats.completed}/${stats.total} 完成，${stats.failed} 失败` :
                     `${stats.completed}/${stats.total} 完成`}
                  </span>
                );
              }
              return null;
            })()}
          </div>
        )}
        placement="right"
        width={400}
        open={uploadDrawerVisible}
        onClose={() => setUploadDrawerVisible(false)}
        extra={
          uploadFiles.length > 0 && (
            <div style={{ display: 'flex', gap: 8 }}>
              {(() => {
                const stats = getBatchStats();
                const hasFailedFiles = stats.failed > 0;
                return hasFailedFiles ? (
                  <Button 
                    size="small" 
                    type="primary"
                    onClick={handleBatchRetry}
                  >
                    重试失败
                  </Button>
                ) : null;
              })()}
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
            </div>
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
            {/* 批次整体进度 */}
            {(() => {
              const stats = getBatchStats();
              if (stats.total > 1) {
                return (
                  <div style={{ 
                    marginBottom: 16, 
                    padding: 12, 
                    backgroundColor: '#f8f9fa', 
                    borderRadius: 8,
                    border: '1px solid #e9ecef'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      marginBottom: 8
                    }}>
                      <span style={{ fontWeight: 'bold', fontSize: 14 }}>
                        批量上传进度
                      </span>
                      <span style={{ fontSize: 12, color: '#666' }}>
                        {stats.completed + stats.failed}/{stats.total} 个文件
                      </span>
                    </div>
                    <Progress
                      percent={stats.overallProgress}
                      size="small"
                      status={stats.failed > 0 ? 'exception' : stats.processing > 0 ? 'active' : 'success'}
                      showInfo={true}
                      format={(percent) => `${percent}%`}
                    />
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      fontSize: 12,
                      color: '#666',
                      marginTop: 4
                    }}>
                      <span>✅ 成功: {stats.completed}</span>
                      {stats.processing > 0 && <span>⏳ 处理中: {stats.processing}</span>}
                      {stats.failed > 0 && <span style={{ color: '#ff4d4f' }}>❌ 失败: {stats.failed}</span>}
                    </div>
                  </div>
                );
              }
              return null;
            })()}
            
            {/* 单个文件状态列表 */}
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
                  handleRetryFile(fileId);
                }}
                onRemove={(fileId) => {
                  setUploadFiles(prev => prev.filter(f => f.id !== fileId));
                }}
              />
            ))}
          </div>
        )}
      </Drawer>

      {/* 搜索模态框 */}
      <Modal
        title="智能搜索"
        open={searchModalVisible}
        onCancel={() => setSearchModalVisible(false)}
        width={800}
        footer={[
          <Button key="reset" onClick={resetSearchFilters}>
            重置过滤器
          </Button>,
          <Button key="cancel" onClick={() => setSearchModalVisible(false)}>
            取消
          </Button>,
          <Button key="search" type="primary" loading={searchLoading} onClick={performSearch}>
            搜索
          </Button>
        ]}
      >
        <div style={{ marginBottom: '16px' }}>
          <Input.Search
            placeholder="输入搜索关键词..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={performSearch}
            enterButton="搜索"
            size="large"
          />
        </div>

        {/* 过滤器 */}
        <div style={{ marginBottom: '16px', padding: '16px', background: '#f5f5f5', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
            <FilterOutlined style={{ marginRight: '8px' }} />
            <span style={{ fontWeight: 'bold' }}>搜索过滤器</span>
          </div>
          
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <div style={{ marginBottom: '8px' }}>分类筛选：</div>
              <Select
                mode="multiple"
                placeholder="选择分类"
                style={{ width: '100%' }}
                value={searchFilters.categories}
                onChange={(value) => setSearchFilters(prev => ({ ...prev, categories: value }))}
                options={categories.map(cat => ({ label: cat.name, value: cat.name }))}
              />
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '8px' }}>合集筛选：</div>
              <Select
                mode="multiple"
                placeholder="选择合集"
                style={{ width: '100%' }}
                value={searchFilters.collections}
                onChange={(value) => setSearchFilters(prev => ({ ...prev, collections: value }))}
                options={customCollections.map(col => ({ label: col.name, value: col.name }))}
              />
            </Col>
            <Col span={8}>
              <div style={{ marginBottom: '8px' }}>文件类型：</div>
              <Select
                placeholder="选择类型"
                style={{ width: '100%' }}
                value={searchFilters.modality}
                onChange={(value) => setSearchFilters(prev => ({ ...prev, modality: value }))}
                allowClear
                options={[
                  { label: '文本', value: 'text' },
                  { label: '图片', value: 'image' },
                  { label: 'PDF', value: 'pdf' }
                ]}
              />
            </Col>
            <Col span={8}>
              <div style={{ marginBottom: '8px' }}>分类角色：</div>
              <Select
                placeholder="选择角色"
                style={{ width: '100%' }}
                value={searchFilters.role}
                onChange={(value) => setSearchFilters(prev => ({ ...prev, role: value }))}
                allowClear
                options={[
                  { label: '主分类', value: 'primary_system' },
                  { label: '次分类', value: 'secondary_system' },
                  { label: '用户规则', value: 'user_rule' }
                ]}
              />
            </Col>
            <Col span={8}>
              <div style={{ marginBottom: '8px' }}>分类来源：</div>
              <Select
                placeholder="选择来源"
                style={{ width: '100%' }}
                value={searchFilters.source}
                onChange={(value) => setSearchFilters(prev => ({ ...prev, source: value }))}
                allowClear
                options={[
                  { label: 'AI分类', value: 'ml' },
                  { label: '规则分类', value: 'heuristic' },
                  { label: '用户规则', value: 'rule' }
                ]}
              />
            </Col>
            <Col span={24}>
              <div style={{ marginBottom: '8px' }}>置信度范围：</div>
              <Slider
                range
                min={0}
                max={1}
                step={0.1}
                value={searchFilters.confidence}
                onChange={(value) => setSearchFilters(prev => ({ ...prev, confidence: value as [number, number] }))}
                marks={{
                  0: '0%',
                  0.5: '50%',
                  1: '100%'
                }}
              />
            </Col>
          </Row>
        </div>

        {/* 搜索结果 */}
        {searchResults.length > 0 && (
          <div>
            <div style={{ marginBottom: '12px', fontWeight: 'bold' }}>
              搜索结果 ({searchResults.length} 条)
            </div>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  style={{
                    padding: '12px',
                    border: '1px solid #e8e8e8',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    cursor: 'pointer'
                  }}
                  onClick={() => {
                    // 跳转到文档详情或所属合集
                    if (result.category_name) {
                      navigate(`/collection/${encodeURIComponent(result.category_name)}`);
                      setSearchModalVisible(false);
                    }
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                    {result.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                    {result.text?.substring(0, 150)}...
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {result.category_name && (
                      <Tag color="blue">📁 {result.category_name}</Tag>
                    )}
                    <Tag color="green">📊 {Math.round((result.score || 0) * 100)}%</Tag>
                    <Tag color="orange">📅 {result.created_at?.split('T')[0]}</Tag>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* 创建合集模态框 */}
      <CreateCollectionModal
        open={createCollectionModalVisible}
        onCancel={() => setCreateCollectionModalVisible(false)}
        onSuccess={handleCreateCollectionSuccess}
      />

      {/* 搜索覆盖层 */}
      <SearchOverlay
        visible={searchOverlayVisible}
        onClose={() => setSearchOverlayVisible(false)}
      />
    </MainLayout>
  );
}