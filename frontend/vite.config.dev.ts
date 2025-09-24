import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 本地开发环境配置
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,  // 匹配实际端口
    proxy: {
      '/api': {
        target: 'https://pkb.kmchat.cloud',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path,
      }
    }
  }
});
