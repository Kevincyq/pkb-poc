import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Spin, Alert, Button, Space } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useAuth } from '../../stores/AuthContext';
import AuthService from '../../services/authService';
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
        // 后端已经返回了用户信息，直接保存
        const userParam = searchParams.get('user');
        
        if (userParam) {
          // 解析用户信息
          const userInfo = JSON.parse(decodeURIComponent(userParam));
          console.log('✅ User info from backend:', userInfo);
          
          // 保存所有认证信息
          localStorage.setItem('auth_token', token);
          localStorage.setItem('auth_user', JSON.stringify(userInfo));
          localStorage.setItem('cloud_connected', 'true');
          
          // 更新Context状态
          setCloudConnected(true);
          
          // 立即跳转（不需要等待API调用或显示成功页面）
          console.log('✅ Redirecting to home page with full reload');
          window.location.href = '/';
        } else {
          // 如果没有用户信息，降级为旧逻辑（调用API）
          console.log('⚠️ No user info in URL, falling back to API call');
          try {
            const userInfo = await AuthService.getCurrentUser();
            localStorage.setItem('auth_user', JSON.stringify(userInfo));
            localStorage.setItem('cloud_connected', 'true');
            setCloudConnected(true);
            window.location.href = '/';
          } catch (e) {
            console.error('Failed to get user info:', e);
            setStatus('error');
            setError('获取用户信息失败');
          }
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
