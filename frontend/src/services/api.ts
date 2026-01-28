/**
 * API服务 - 使用Mock数据模式
 * 当后端API未完成时，使用mock数据方便本地调试
 * 
 * 要切换到真实API，设置环境变量: VITE_USE_MOCK_API=false
 */

import axios, { AxiosRequestConfig, AxiosResponse, AxiosInstance } from 'axios';
import mockApi from './mockApi';

// 检查是否使用Mock API（默认使用Mock）
const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== 'false';

console.log('🔧 API Mode:', USE_MOCK_API ? 'MOCK (本地调试模式)' : 'REAL (真实API)');

// 创建API实例
let api: AxiosInstance | any;

if (USE_MOCK_API) {
  // 创建兼容axios接口的mock API包装器
  api = {
    get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
      console.log('🎭 [MOCK] GET:', url);
      return mockApi.get<T>(url, config);
    },
    post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
      console.log('🎭 [MOCK] POST:', url, data);
      return mockApi.post<T>(url, data, config);
    },
    put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
      console.log('🎭 [MOCK] PUT:', url, data);
      return mockApi.put<T>(url, data, config);
    },
    delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
      console.log('🎭 [MOCK] DELETE:', url);
      return mockApi.delete<T>(url, config);
    },
    // 为了兼容性，添加其他axios方法
    patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
      console.log('🎭 [MOCK] PATCH:', url, data);
      return mockApi.put<T>(url, data, config);
    },
    interceptors: {
      request: { use: () => {}, eject: () => {} },
      response: { use: () => {}, eject: () => {} },
    },
  };
} else {
  // 使用真实API
  // API基础URL配置
  const baseURL = '/api';
  const finalBaseURL = '/api';
  console.log('🎯 Selected baseURL:', baseURL);
  console.log('🔧 Final baseURL:', finalBaseURL);

  api = axios.create({
    baseURL: finalBaseURL,
    headers: {
      'Content-Type': 'application/json',
    },
    httpsAgent: false,
    maxRedirects: 0,
    validateStatus: (status) => status < 600,
  });

  // 请求拦截器
  api.interceptors.request.use(
    (config: any) => {
      if (config.url && config.url.length > 1) {
        config.url = config.url.replace(/\/+$/, '');
        console.log('🔧 Cleaned URL:', config.url);
      }
      
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('🔐 Added auth header');
      }
      
      console.log('🌐 Request:', config.method?.toUpperCase(), config.url);
      return config;
    },
    (error: any) => {
      console.error('❌ Request error:', error);
      return Promise.reject(error);
    }
  );

  // 响应拦截器
  api.interceptors.response.use(
    (response: any) => {
      return response;
    },
    async (error: any) => {
      if (!error.response) {
        console.error('❌ Network error:', error.message);
        return Promise.reject(error);
      }

      const status = error.response.status;
      const errorDetail = error.response.data?.detail || '';
      const errorUrl = error.config?.url || '';
      
      console.error(`❌ API Error [${status}]:`, errorUrl, errorDetail);
      return Promise.reject(error);
    }
  );
}

export default api;