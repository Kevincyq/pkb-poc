import axios from 'axios';

// 检查环境变量
console.log('🔍 Environment check:', {
  'import.meta.env.DEV': import.meta.env.DEV,
  'import.meta.env.PROD': import.meta.env.PROD,
  'import.meta.env.MODE': import.meta.env.MODE,
  'import.meta.env.VITE_API_BASE_URL': import.meta.env.VITE_API_BASE_URL,
  'window.location': window.location.href
});

// API基础URL配置
// 强制使用代理路径，避免混合内容问题
// 永远使用 /api 路径，让Vercel代理到后端
const baseURL = '/api';
const finalBaseURL = '/api';
console.log('🎯 Selected baseURL:', baseURL);
console.log('🔧 Final baseURL:', finalBaseURL);

const api = axios.create({
  baseURL: finalBaseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  // 强制使用HTTPS，防止Mixed Content错误
  httpsAgent: false,
  maxRedirects: 0, // 禁用自动重定向，防止HTTPS->HTTP
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 自动添加认证头（如果存在token）
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔐 Adding auth header with token:', token.substring(0, 20) + '...');
    } else {
      console.log('⚠️ No auth token found in localStorage');
    }
    
    console.log('🌐 Making request to:', config.url);
    console.log('📋 Full config:', config);
    console.log('🏠 Base URL:', config.baseURL);
    console.log('🎯 Final URL:', (config.baseURL || '') + (config.url || ''));
    return config;
  },
  (error) => {
    console.error('❌ Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('Response received:', response);
    return response;
  },
  async (error) => {
    if (error.response) {
      console.error('API Error Response:', error.response.data);
      console.error('API Error Status:', error.response.status);
      console.error('API Error URL:', error.config?.url);
      console.error('API Error Headers:', error.response.headers);
      
      // 处理401未授权错误 - 但只在确实是认证失败时才重定向
      if (error.response.status === 401) {
        const errorDetail = error.response.data?.detail;
        console.log('🔐 401 Unauthorized - error detail:', errorDetail);
        
        // 检查是否是URL路径问题（如尾随斜杠）
        const errorUrl = error.config?.url || '';
        if (errorUrl.includes('collection/') || errorDetail?.includes('authorization header')) {
          console.log('⚠️ 401 with collection API or missing authorization');
          console.log('  - This might be a temporary auth issue, not clearing token');
          console.log('  - Waiting for other requests to complete');
          // 不立即清除token，等所有请求完成后再判断
        } else {
          console.log('🔐 401 Unauthorized - clearing invalid token');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          localStorage.removeItem('cloud_connected');
          
          // 如果不在登录页面，重定向到登录页
          if (window.location.pathname !== '/login' && window.location.pathname !== '/auth/callback') {
            console.log('🔄 Redirecting to login page');
            window.location.href = '/login';
          }
        }
      }
      
    } else if (error.request) {
      console.error('API Request Error (No Response):', error.request);
    } else {
      console.error('API Error Setup:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;