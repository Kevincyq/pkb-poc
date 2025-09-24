import api from './api';

export interface CustomCollection {
  id: string;
  name: string;
  description?: string;
  content_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateCollectionRequest {
  name: string;
  description?: string;
  auto_match?: boolean;  // 新增：智能匹配参数
}

export interface UpdateCollectionRequest {
  name?: string;
  description?: string;
}

// 获取所有自建合集
export const getCustomCollections = async (): Promise<CustomCollection[]> => {
  try {
    const response = await api.get<CustomCollection[]>('/collection/');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch custom collections:', error);
    throw error;
  }
};

// 创建新合集
export const createCollection = async (data: CreateCollectionRequest): Promise<CustomCollection> => {
  try {
    const response = await api.post<CustomCollection>('/collection/', data);
    return response.data;
  } catch (error) {
    console.error('Failed to create collection:', error);
    throw error;
  }
};

// 更新合集
export const updateCollection = async (
  id: string, 
  data: UpdateCollectionRequest
): Promise<CustomCollection> => {
  try {
    console.log('Updating collection with ID:', id, 'Data:', data);
    const response = await api.put<CustomCollection>(`/collection/${id}`, data);
    console.log('Update response:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Failed to update collection:', error);
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
    throw new Error(error.response?.data?.detail || error.message || '更新失败');
  }
};

// 删除合集
export const deleteCollection = async (id: string): Promise<void> => {
  try {
    console.log('Deleting collection with ID:', id);
    console.log('ID type:', typeof id);
    console.log('Making DELETE request to:', `/collection/${id}`);
    
    // 首先检查API是否存在
    const testResponse = await api.get('/collection/');
    console.log('Collection API exists, status:', testResponse.status);
    
    const response = await api.delete(`/collection/${id}`);
    
    console.log('Delete response status:', response.status);
    console.log('Delete response data:', response.data);
    
    if (response.status !== 200) {
      throw new Error(`Unexpected response status: ${response.status}`);
    }
    
  } catch (error: any) {
    console.error('Failed to delete collection:', error);
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      config: error.config?.url
    });
    
    // 检查是否是404错误（API不存在）
    if (error.response?.status === 404) {
      throw new Error('删除功能暂不可用：远程服务器上的API尚未部署');
    }
    
    // 提供更详细的错误信息
    let errorMessage = '删除失败';
    if (error.response) {
      errorMessage = error.response.data?.detail || `服务器错误 (${error.response.status})`;
    } else if (error.request) {
      errorMessage = '网络请求失败，请检查网络连接';
    } else {
      errorMessage = error.message || '未知错误';
    }
    
    throw new Error(errorMessage);
  }
};

// 获取合集中的文档
export const getCollectionContents = async (id: string) => {
  try {
    const response = await api.get(`/collection/${id}/contents`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch collection contents:', error);
    throw error;
  }
};
