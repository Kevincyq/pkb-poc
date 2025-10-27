import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Spin, Alert, Button, Space } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useAuth } from '../../stores/AuthContext';
import AuthService from '../../services/authService';
import { parseJWT } from '../../utils/jwt';
import './AuthCallback.css';

const { Title, Text } = Typography;

const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setCloudConnected } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    handleOAuthCallback();
  }, []);

  const handleOAuthCallback = async () => {
    try {
      // 检查是否是后端直接重定向（带token）
      const token = searchParams.get('token');
      const success = searchParams.get('success');
      const errorParam = searchParams.get('error');
      
      // 检查是否有错误errors
      if (success === 'false' || errorParam) {
        setStatus('error');
        setError(errorParam || 'OAuth授权失败');
        return;
      }
      
      if (token && success === 'true') {
        // 保存token
        console.log('✅ Saving token to localStorage:', token.substring(0, 20) + '...');
        localStorage.setItem('auth_token', token);
        localStorage.setItem('cloud_connected', 'true');
        
        // 从JWT中提取用户信息
        try {
          const payload = parseJWT(token);
          if (!payload) {
            throw new Error('Failed to parse JWT token');
          }
          
          // 检查是新JWT（包含完整信息）还是旧JWT（只有user_id和email）
          if (payload.display_name !== undefined) {
            // 新JWT：包含完整用户信息
            const userInfo = {
              id: payload.user_id,
              email: payload.email,
              display_name: payload.display_name,
              avatar_url: payload.avatar_url,
              is_google_user: payload.is_google_user
            };
            localStorage.setItem('auth_user', JSON.stringify(userInfo));
            console.log('✅ User info extracted from new JWT:', userInfo);
            
            // 更新Context状态
            setCloudConnected(true);
            
            // 设置成功状态（会显示成功页面）
            setStatus('success');
            setMessage('授权成功！');
            
            // 短暂显示成功页面后跳转
            setTimeout(() => {
              console.log('✅ Redirecting to home page with full reload');
              window.location.href = '/';
            }, 600);
          } else {
            // 旧JWT：调用API获取完整用户信息
            console.log('⚠️ Old JWT format detected, fetching user info from API');
            const userInfo = await AuthService.getCurrentUser();
            localStorage.setItem('auth_user', JSON.stringify(userInfo));
            console.log('✅ User info fetched from API:', userInfo);
            
            // 更新Context状态
            setCloudConnected(true);
            
            // 设置成功状态
            setStatus('success');
            setMessage('授权成功！');
            
            setTimeout(() => {
              console.log('✅ Redirecting to home page with full reload');
              window.location.href = '/';
            }, 600);
          }
        } catch (e) {
          console.error('Failed to extract user info:', e);
          setStatus('error');
          setError('授权信息处理失败');
        }
        return;
      }
      
      // 如果没有token，说明这不是后端重定向的回调
      // 这种情况不应该发生，因为Google OAuth总是回调到后端
      setStatus('error');
      setError('未识别的回调格式，请联系管理员');
    } catch (error: any) {
      console.error('OAuth callback error:', error);
      setStatus('error');
      setError(error.message || 'OAuth回调处理失败');
    }
  };

  const handleRetry = () => {
    navigate('/login');
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="auth-callback-container">
      <div className="auth-callback-background">
        <Card className="auth-callback-card" bordered={false}>
          <div className="auth-callback-content">
            {status === 'loading' && (
              <>
                <Spin size="large" />
                <Title level={3} className="auth-callback-title">
                  正在处理授权...
                </Title>
                <Text type="secondary" className="auth-callback-message">
                  {message}
                </Text>
              </>
            )}

            {status === 'success' && (
              <>
                <CheckCircleOutlined className="success-icon" />
                <Title level={3} className="auth-callback-title success">
                  授权成功
                </Title>
                <Text type="secondary" className="auth-callback-message">
                  {message}
                </Text>
                <div className="auth-callback-actions">
                  <Button type="primary" onClick={handleGoHome}>
                    进入主界面
                  </Button>
                </div>
              </>
            )}

            {status === 'error' && (
              <>
                <CloseCircleOutlined className="error-icon" />
                <Title level={3} className="auth-callback-title error">
                  授权失败
                </Title>
                <Alert
                  message="授权失败"
                  description={error}
                  type="error"
                  showIcon
                  className="auth-callback-alert"
                />
                <div className="auth-callback-actions">
                  <Space>
                    <Button type="primary" onClick={handleRetry}>
                      重新登录
                    </Button>
                    <Button onClick={handleGoHome}>
                      返回首页
                    </Button>
                  </Space>
                </div>
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AuthCallback;
