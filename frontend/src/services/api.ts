import axios from 'axios';

// 检查环境变量
console.log('🔍 Environment check:', {
  'import.meta.env.DEV': import.meta.env.DEV,
  'import.meta.env.PROD': import.meta.env.PROD,
  'import.meta.env.MODE': import.meta.env.MODE,
  'window.location': window.location.href
});

const baseURL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.DEV ? '/api' : 'https://pkb.kmchat.cloud/api');
console.log('🎯 Selected baseURL:', baseURL);

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
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
  (error) => {
    if (error.response) {
      console.error('API Error Response:', error.response.data);
      console.error('API Error Status:', error.response.status);
      console.error('API Error Headers:', error.response.headers);
    } else if (error.request) {
      console.error('API Request Error (No Response):', error.request);
    } else {
      console.error('API Error Setup:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;