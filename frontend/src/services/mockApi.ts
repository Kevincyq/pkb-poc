/**
 * Mock API服务 - 模拟所有后端API调用
 * 用于本地开发和调试，当后端API未完成时使用
 */

import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  mockCategories,
  mockDocuments,
  mockCollections,
  mockQAHistory,
  mockRecommendedQuestions,
  generateMockQAResponse,
  generateMockUploadResponse,
  generateMockProcessingStatus,
  generateMockSearchResponse,
} from './mockData';

// 模拟延迟
const delay = (ms: number = 300) => new Promise(resolve => setTimeout(resolve, ms));

// 创建mock响应
const createMockResponse = <T>(data: T, status: number = 200): AxiosResponse<T> => {
  return {
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {} as any,
  };
};

/**
 * Mock API实现
 */
class MockApi {
  // 存储上传的文件信息
  private uploads: Map<string, any> = new Map();
  // 存储合集数据（支持增删改）
  private collections: any[] = [...mockCollections];
  // 存储问答历史
  private qaHistory: any[] = [...mockQAHistory];

  /**
   * 处理GET请求
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    await delay(200 + Math.random() * 300);

    // 分类统计
    if (url === '/search/categories/stats' || url.startsWith('/search/categories/stats')) {
      return createMockResponse<T>({
        categories: mockCategories,
      } as T);
    }

    // 按分类搜索
    if (url.startsWith('/search/category/')) {
      const categoryName = decodeURIComponent(url.split('/search/category/')[1].split('?')[0]);
      const params = new URLSearchParams(url.split('?')[1] || '');
      const query = params.get('q') || '';
      const limit = parseInt(params.get('top_k') || '20');

      const category = mockCategories.find(c => c.name === categoryName) || mockCategories[0];
      const filteredDocs = mockDocuments
        .filter(doc => 
          (!query || doc.title.toLowerCase().includes(query.toLowerCase()) || 
           doc.text?.toLowerCase().includes(query.toLowerCase())) &&
          doc.category_name === categoryName
        )
        .slice(0, limit);

      return createMockResponse<T>({
        category: {
          id: category.id,
          name: category.name,
          color: category.color,
        },
        results: filteredDocs,
        total: filteredDocs.length,
      } as T);
    }

    // 搜索
    if (url.startsWith('/search')) {
      const params = new URLSearchParams(url.split('?')[1] || '');
      const query = params.get('q') || '';
      const limit = parseInt(params.get('top_k') || '20');

      return createMockResponse<T>(generateMockSearchResponse(query, limit) as T);
    }

    // 获取合集列表
    if (url === '/collection' || url === '/collection/') {
      return createMockResponse<T>(this.collections as T);
    }

    // 获取合集详情
    if (url.match(/^\/collection\/[^/]+$/)) {
      const id = url.split('/collection/')[1];
      const collection = this.collections.find(c => c.id === id);
      if (collection) {
        return createMockResponse<T>(collection as T);
      }
      return createMockResponse<T>({} as T, 404);
    }

    // 获取合集内容
    if (url.match(/^\/collection\/[^/]+\/contents$/)) {
      const id = url.split('/collection/')[1].split('/contents')[0];
      const filteredDocs = mockDocuments.slice(0, 10);
      return createMockResponse<T>({
        collection_id: id,
        contents: filteredDocs,
        total: filteredDocs.length,
      } as T);
    }

    // 获取处理状态
    if (url.startsWith('/ingest/status/')) {
      const contentId = url.split('/ingest/status/')[1];
      const upload = this.uploads.get(contentId);
      if (upload) {
        return createMockResponse<T>(upload as T);
      }
      // 生成新的状态
      const status = generateMockProcessingStatus(contentId, 'document.pdf');
      this.uploads.set(contentId, status);
      return createMockResponse<T>(status as T);
    }

    // 验证文件
    if (url.startsWith('/document/validate/')) {
      return createMockResponse<T>({
        valid: true,
        message: '文件格式有效',
      } as T);
    }

    // 问答历史
    if (url.startsWith('/qa/history')) {
      let sessionId = 'default';
      let limit = 100;
      
      // 处理URL参数
      if (url.includes('?')) {
        const urlParams = new URLSearchParams(url.split('?')[1]);
        sessionId = urlParams.get('session_id') || 'default';
        limit = parseInt(urlParams.get('limit') || '100');
      }
      
      // 处理config.params（qaService使用这种方式）
      if (config?.params) {
        sessionId = (config.params as any).session_id || sessionId;
        limit = (config.params as any).limit || limit;
      }

      return createMockResponse<T>({
        session_id: String(sessionId),
        history: this.qaHistory.slice(0, Number(limit)),
        total: this.qaHistory.length,
      } as T);
    }

    // 问答测试
    if (url === '/qa/test') {
      return createMockResponse<T>({
        status: 'ok',
        message: '问答服务正常',
      } as T);
    }

    // 推荐问题
    if (url === '/qa/recommended-questions' || url.startsWith('/qa/recommended-questions')) {
      return createMockResponse<T>({
        questions: mockRecommendedQuestions,
      } as T);
    }

    // 默认返回空数据
    return createMockResponse<T>({} as T);
  }

  /**
   * 处理POST请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    await delay(300 + Math.random() * 500);

    // 文件上传
    if (url === '/ingest/upload-smart' || url === '/ingest/upload') {
      const file = data instanceof FormData ? (data as FormData).get('file') as File : null;
      if (file) {
        const fileName = file.name;
        const fileSize = file.size;
        const uploadResponse = generateMockUploadResponse(fileName, fileSize);
        
        // 模拟上传进度
        if (config?.onUploadProgress) {
          const total = fileSize;
          for (let loaded = 0; loaded <= total; loaded += total / 10) {
            await delay(100);
            if (config.onUploadProgress) {
              config.onUploadProgress({
                loaded,
                total,
                progress: (loaded / total) * 100,
              } as any);
            }
          }
        }

        // 保存上传信息
        const processingStatus = generateMockProcessingStatus(uploadResponse.content_id, fileName);
        this.uploads.set(uploadResponse.content_id, processingStatus);

        return createMockResponse<T>(uploadResponse as T);
      }
    }

    // 批量上传
    if (url === '/ingest/upload-multiple') {
      const formData = data as FormData;
      const files = formData.getAll('files') as File[];
      
      const results = files.map((file, index) => {
        try {
          const uploadResponse = generateMockUploadResponse(file.name, file.size);
          const processingStatus = generateMockProcessingStatus(uploadResponse.content_id, file.name);
          this.uploads.set(uploadResponse.content_id, processingStatus);
          return {
            index,
            filename: file.name,
            status: 'success' as const,
            result: uploadResponse,
          };
        } catch (error) {
          return {
            index,
            filename: file.name,
            status: 'error' as const,
            error: '上传失败',
          };
        }
      });

      return createMockResponse<T>({
        status: 'success',
        total_files: files.length,
        success_count: results.filter(r => r.status === 'success').length,
        error_count: results.filter(r => r.status === 'error').length,
        results,
        message: '批量上传完成',
      } as T);
    }

    // 创建合集
    if (url === '/collection' || url === '/collection/') {
      const newCollection = {
        id: 'coll_' + Date.now(),
        name: data.name,
        description: data.description || '',
        content_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      this.collections.push(newCollection);
      return createMockResponse<T>(newCollection as T);
    }

    // 问答
    if (url === '/qa/ask' || url.startsWith('/qa/ask')) {
      const question = data?.question || '';
      const response = generateMockQAResponse(question);
      
      // 保存到历史
      this.qaHistory.push({
        id: response.qa_id,
        question: response.question,
        answer: response.answer,
        session_id: response.session_id,
        confidence: response.confidence,
        created_at: new Date().toISOString(),
      });

      return createMockResponse<T>(response as T);
    }

    // 问答反馈
    if (url === '/qa/feedback' || url.startsWith('/qa/feedback')) {
      return createMockResponse<T>({
        success: true,
        message: '反馈已提交',
      } as T);
    }

    // 默认返回成功
    return createMockResponse<T>({ success: true } as T);
  }

  /**
   * 处理PUT请求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    await delay(200 + Math.random() * 300);

    // 更新合集
    if (url.match(/^\/collection\/[^/]+$/)) {
      const id = url.split('/collection/')[1];
      const index = this.collections.findIndex(c => c.id === id);
      if (index >= 0) {
        this.collections[index] = {
          ...this.collections[index],
          ...data,
          updated_at: new Date().toISOString(),
        };
        return createMockResponse<T>(this.collections[index] as T);
      }
      return createMockResponse<T>({} as T, 404);
    }

    return createMockResponse<T>({ success: true } as T);
  }

  /**
   * 处理DELETE请求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    await delay(200 + Math.random() * 300);

    // 删除合集
    if (url.match(/^\/collection\/[^/]+$/)) {
      const id = url.split('/collection/')[1];
      const index = this.collections.findIndex(c => c.id === id);
      if (index >= 0) {
        this.collections.splice(index, 1);
        return createMockResponse<T>({ success: true } as T);
      }
      return createMockResponse<T>({} as T, 404);
    }

    // 删除文档
    if (url.match(/^\/document\/[^/]+$/)) {
      const id = url.split('/document/')[1];
      return createMockResponse<T>({
        success: true,
        message: '文档已删除',
      } as T);
    }

    return createMockResponse<T>({ success: true } as T);
  }
}

// 创建单例
const mockApi = new MockApi();

export default mockApi;

