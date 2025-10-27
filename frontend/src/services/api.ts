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
    // ✅ 强制移除URL尾随斜杠（避免FastAPI路由问题）
    if (config.url && config.url.length > 1) {
      config.url = config.url.replace(/\/+$/, '');  // 移除所有尾随斜杠
      console.log('🔧 Cleaned URL:', config.url);
    }
    
    // ✅ 自动添加认证头（如果存在token）
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔐 Added auth header');
    } else {
      console.log('⚠️ No auth token found');
    }
    
    console.log('🌐 Request:', config.method?.toUpperCase(), config.url);
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
    // 成功响应直接返回
    return response;
  },
  async (error) => {
    if (!error.response) {
      // 网络错误
      console.error('❌ Network error:', error.message);
      return Promise.reject(error);
    }

    const status = error.response.status;
    const errorDetail = error.response.data?.detail || '';
    const errorUrl = error.config?.url || '';
    
    console.error(`❌ API Error [${status}]:`, errorUrl, errorDetail);
    
    // ✅ 处理401错误
    if (status === 401) {
      // 检查是否是在认证页面
      const isAuthPage = window.location.pathname === '/login' || 
                        window.location.pathname === '/auth/callback';
      
      if (isAuthPage) {
        console.log('ℹ️ 401 in auth page - ignoring');
        return Promise.reject(error);
      }
      
      // 检查token是否存在
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.log('⚠️ No token - user not logged in');
        return Promise.reject(error);
      }
      
      // ✅ 检查是否是明确的认证失败（而不是路由不存在）
      const isAuthFailure = errorDetail.includes('authorization header') || 
                           errorDetail.includes('Missing') ||
                           errorDetail.includes('Invalid token') ||
                           errorDetail.includes('User not found');
      
      if (isAuthFailure) {
        console.log('🔐 Authentication failure - logging out');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('cloud_connected');
        
        setTimeout(() => {
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }, 1500);
      } else {
        // ✅ 路由不存在或其他原因导致的401，静默忽略
        console.log('ℹ️ 401 from route issue, ignoring:', errorUrl);
      }
    }
    
    // 其他错误
    return Promise.reject(error);
  }
);

export default api;