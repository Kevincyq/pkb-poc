import api from '../services/api';

// 登录请求类型
export interface LoginRequest {
  username: string;
  password: string;
}

// 登录响应类型
export interface LoginResponse {
  success: boolean;
  user: {
    id: string;
    email: string;
    display_name: string;
    avatar_url?: string;
    is_google_user: boolean;
  };
  token: string;
  message: string;
  drive_access_confirmed?: boolean;
}

// Google OAuth响应类型
export interface GoogleAuthResponse {
  auth_url: string;
  state: string;
  provider: string;
}

// Google OAuth回调响应类型
export interface GoogleCallbackResponse {
  success: boolean;
  user: {
    id: string;
    email: string;
    display_name: string;
    avatar_url?: string;
    is_google_user: boolean;
  };
  token: string;
  drive_access_confirmed: boolean;
  redirect_url: string;
  error?: string;
}

// 用户信息响应类型
export interface UserInfoResponse {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  is_google_user: boolean;
}

// 认证服务类
export class AuthService {
  /**
   * 用户登录（支持test用户和Google用户）
   */
  static async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await api.post('/auth/login', credentials);
      return response.data;
    } catch (error: any) {
      console.error('Login error:', error);
      throw new Error(error.response?.data?.detail || '登录失败');
    }
  }

  /**
   * 启动Google OAuth认证
   */
  static async startGoogleAuth(): Promise<GoogleAuthResponse> {
    try {
      const response = await api.get('/auth/google');
      return response.data;
    } catch (error: any) {
      console.error('Google OAuth start error:', error);
      throw new Error(error.response?.data?.detail || 'Google OAuth启动失败');
    }
  }

  /**
   * 处理Google OAuth回调
   */
  static async handleGoogleCallback(code: string, state: string): Promise<GoogleCallbackResponse> {
    try {
      const response = await api.get(`/auth/callback/gdrive?code=${code}&state=${state}`);
      return response.data;
    } catch (error: any) {
      console.error('Google OAuth callback error:', error);
      throw new Error(error.response?.data?.detail || 'OAuth回调处理失败');
    }
  }

  /**
   * 获取当前用户信息
   */
  static async getCurrentUser(): Promise<UserInfoResponse> {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error: any) {
      console.error('Get current user error:', error);
      throw new Error(error.response?.data?.detail || '获取用户信息失败');
    }
  }

  /**
   * 验证Token有效性
   */
  static async validateToken(token: string): Promise<boolean> {
    try {
      const response = await api.get('/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      return response.status === 200;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }

  /**
   * 登出（清除本地存储）
   */
  static logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('cloud_connected');
  }

  /**
   * 获取存储的Token
   */
  static getStoredToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  /**
   * 获取存储的用户信息
   */
  static getStoredUser(): any | null {
    try {
      const userStr = localStorage.getItem('auth_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Failed to parse stored user:', error);
      return null;
    }
  }

  /**
   * 获取云盘连接状态
   */
  static getCloudConnectedStatus(): boolean {
    return localStorage.getItem('cloud_connected') === 'true';
  }

  /**
   * 设置云盘连接状态
   */
  static setCloudConnectedStatus(connected: boolean): void {
    localStorage.setItem('cloud_connected', connected.toString());
  }

  /**
   * 检查是否已登录
   */
  static isAuthenticated(): boolean {
    const token = this.getStoredToken();
    const user = this.getStoredUser();
    return !!(token && user);
  }

  /**
   * 获取认证头
   */
  static getAuthHeaders(): Record<string, string> {
    const token = this.getStoredToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
}

export default AuthService;
