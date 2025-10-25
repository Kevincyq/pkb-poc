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
// 优先使用环境变量（Vercel会在构建时注入）
// 本地开发时的fallback逻辑
const baseURL = import.meta.env.VITE_API_BASE_URL || 
  (window.location.hostname === 'localhost' 
    ? '/api'  // 本地开发 - 使用Vite代理
    : '/api'  // 生产环境 - 使用Vercel代理
  );

// 强制使用代理，避免混合内容问题
const finalBaseURL = baseURL.startsWith('http://') ? '/api' : baseURL;
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
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
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
      console.error('API Error Headers:', error.response.headers);
      
      // 处理401未授权错误 - 清除无效token
      if (error.response.status === 401) {
        console.log('🔐 401 Unauthorized - clearing invalid token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('cloud_connected');
        
        // 如果不在登录页面，重定向到登录页
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
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