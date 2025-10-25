import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';

// 用户信息类型
export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  is_google_user: boolean;
}

// 认证状态类型
export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  cloudConnected: boolean;
}

// 认证上下文类型
interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
  setCloudConnected: (connected: boolean) => void;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null,
    isLoading: true,
    cloudConnected: false,
  });

  // 从localStorage加载认证状态
  useEffect(() => {
    const loadAuthState = () => {
      try {
        const token = localStorage.getItem('auth_token');
        const userStr = localStorage.getItem('auth_user');
        const cloudConnected = localStorage.getItem('cloud_connected') === 'true';

        if (token && userStr) {
          const user = JSON.parse(userStr);
          setAuthState({
            isAuthenticated: true,
            user,
            token,
            isLoading: false,
            cloudConnected,
          });
        } else {
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
          }));
        }
      } catch (error) {
        console.error('Failed to load auth state:', error);
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
        }));
      }
    };

    loadAuthState();
  }, []);

  // 保存认证状态到localStorage
  const saveAuthState = (user: User, token: string, cloudConnected: boolean = false) => {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('auth_user', JSON.stringify(user));
    localStorage.setItem('cloud_connected', cloudConnected.toString());
    
    setAuthState({
      isAuthenticated: true,
      user,
      token,
      isLoading: false,
      cloudConnected,
    });
  };

  // 清除认证状态
  const clearAuthState = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('cloud_connected');
    
    setAuthState({
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
      cloudConnected: false,
    });
  };

  // 登录函数
  const login = async (username: string, password: string): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      const response = await api.post('/auth/login', {
        username,
        password,
      });

      const data = response.data;
      
      if (data.success) {
        saveAuthState(data.user, data.token, data.drive_access_confirmed || false);
      } else {
        throw new Error(data.message || '登录失败');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      setAuthState(prev => ({ ...prev, isLoading: false }));
      throw new Error(error.response?.data?.detail || error.message || '登录失败');
    }
  };

  // Google OAuth登录
  const loginWithGoogle = async (): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      const response = await api.get('/auth/google');
      const data = response.data;
      
      if (data.auth_url) {
        // 重定向到Google OAuth页面
        window.location.href = data.auth_url;
      } else {
        throw new Error('未获取到OAuth URL');
      }
    } catch (error: any) {
      console.error('Google OAuth error:', error);
      setAuthState(prev => ({ ...prev, isLoading: false }));
      throw new Error(error.response?.data?.detail || error.message || 'Google OAuth启动失败');
    }
  };

  // 登出函数
  const logout = () => {
    clearAuthState();
  };

  // 检查认证状态
  const checkAuthStatus = async (): Promise<void> => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return;
      }

      const response = await api.get('/auth/me');

      if (response.status === 200) {
        const userStr = localStorage.getItem('auth_user');
        const cloudConnected = localStorage.getItem('cloud_connected') === 'true';
        
        if (userStr) {
          const user = JSON.parse(userStr);
          setAuthState({
            isAuthenticated: true,
            user,
            token,
            isLoading: false,
            cloudConnected,
          });
        }
      }
    } catch (error: any) {
      console.error('Auth status check error:', error);
      // 如果是401错误，API拦截器已经处理了token清除
      // 这里只需要更新状态
      if (error.response?.status === 401) {
        setAuthState({
          isAuthenticated: false,
          user: null,
          token: null,
          isLoading: false,
          cloudConnected: false,
        });
      } else {
        // 其他错误，保持当前状态但停止加载
        setAuthState(prev => ({ ...prev, isLoading: false }));
      }
    }
  };

  // 设置云盘连接状态
  const setCloudConnected = (connected: boolean) => {
    localStorage.setItem('cloud_connected', connected.toString());
    setAuthState(prev => ({
      ...prev,
      cloudConnected: connected,
    }));
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    loginWithGoogle,
    logout,
    checkAuthStatus,
    setCloudConnected,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
