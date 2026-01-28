import React, { createContext, useContext, useState, ReactNode } from 'react';

// 用户信息类型（保留用于兼容性，但不再使用）
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
}

// 认证上下文类型
interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件 - 简化版本，始终返回已认证状态
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // 始终返回已认证状态，不需要登录
  const [authState] = useState<AuthState>({
    isAuthenticated: true,
    user: null,
    token: null,
    isLoading: false,
  });

  // 空函数，保持接口兼容性
  const login = async (_username: string, _password: string): Promise<void> => {
    // 不再需要登录
  };

  const loginWithGoogle = async (): Promise<void> => {
    // 不再需要登录
  };

  const logout = () => {
    // 不再需要登出
  };

  const checkAuthStatus = async (): Promise<void> => {
    // 不再需要检查认证状态
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    loginWithGoogle,
    logout,
    checkAuthStatus,
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
