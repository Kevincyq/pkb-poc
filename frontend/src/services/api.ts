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
  // 禁用URL规范化，避免自动添加尾随斜杠
  validateStatus: (status) => status < 600,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 移除URL尾随斜杠（避免FastAPI路由问题）
    if (config.url && config.url.endsWith('/') && config.url.length > 1) {
      config.url = config.url.slice(0, -1);
      console.log('🔧 Removed trailing slash from URL:', config.url);
    }
    
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
      
      // 处理401未授权错误
      if (error.response.status === 401) {
        const errorDetail = error.response.data?.detail || '';
        const errorUrl = error.config?.url || '';
        
        // 检查是否是在认证页面（这些页面允许401）
        const isAuthPage = window.location.pathname === '/login' || 
                          window.location.pathname === '/auth/callback' ||
                          window.location.pathname.startsWith('/api/auth');
        
        if (isAuthPage) {
          console.log('ℹ️ 401 in auth page - ignoring');
          return Promise.reject(error);
        }
        
        // 检查token是否存在
        const token = localStorage.getItem('auth_token');
        if (!token) {
          console.log('⚠️ No token in localStorage');
          return Promise.reject(error);
        }
        
        // 检查是否是明确的认证失败
        const isAuthFailure = errorDetail.includes('authorization header') || 
                             errorDetail.includes('Missing') ||
                             errorDetail.includes('Invalid token') ||
                             errorDetail.includes('User not found');
        
        if (isAuthFailure) {
          console.log('🔐 Authentication failure detected - clearing token');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          localStorage.removeItem('cloud_connected');
          
          // 延迟重定向
          setTimeout(() => {
            if (window.location.pathname !== '/login' && window.location.pathname !== '/auth/callback') {
              console.log('🔄 Redirecting to login page');
              window.location.href = '/login';
            }
          }, 2000);
        } else {
          // 其他401错误，可能只是路由不存在
          console.log('⚠️ 401 error but not confirmed auth failure, ignoring');
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