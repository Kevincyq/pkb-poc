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
    ? 'http://localhost:8003/api'  // 本地开发
    : 'https://pkb-test.kmchat.cloud/api'  // 默认测试环境
  );
console.log('🎯 Selected baseURL:', baseURL);

const api = axios.create({
  baseURL,
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
    // 强制确保所有请求都使用HTTPS
    if (config.baseURL && config.baseURL.startsWith('http://')) {
      config.baseURL = config.baseURL.replace('http://', 'https://');
      console.log('🔒 Forced HTTPS for baseURL:', config.baseURL);
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
      
      // 处理307重定向到HTTP的问题
      if (error.response.status === 307 && error.response.headers.location) {
        const redirectUrl = error.response.headers.location;
        console.log('🔄 Handling 307 redirect:', redirectUrl);
        
        if (redirectUrl.startsWith('http://')) {
          // 强制使用HTTPS重新请求
          const httpsUrl = redirectUrl.replace('http://', 'https://');
          console.log('🔒 Redirecting to HTTPS:', httpsUrl);
          
          try {
            const newResponse = await api.get(httpsUrl.replace(error.config.baseURL, ''));
            return newResponse;
          } catch (retryError) {
            console.error('❌ HTTPS retry failed:', retryError);
            return Promise.reject(retryError);
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