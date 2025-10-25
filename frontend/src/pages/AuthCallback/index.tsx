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
      // 从URL参数获取code和state
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorParam = searchParams.get('error');

      // 检查是否有错误参数
      if (errorParam) {
        setStatus('error');
        setError(`OAuth授权失败: ${errorParam}`);
        return;
      }

      // 检查必要参数
      if (!code || !state) {
        setStatus('error');
        setError('缺少必要的OAuth参数');
        return;
      }

      setStatus('loading');
      setMessage('正在处理Google OAuth回调...');

      // 调用后端处理OAuth回调
      const result = await AuthService.handleGoogleCallback(code, state);

      if (result.success) {
        // 保存用户信息和Token到localStorage
        localStorage.setItem('auth_token', result.token);
        localStorage.setItem('auth_user', JSON.stringify(result.user));
        localStorage.setItem('cloud_connected', result.drive_access_confirmed.toString());

        // 设置云盘连接状态
        setCloudConnected(result.drive_access_confirmed);

        setStatus('success');
        setMessage('Google OAuth授权成功！');

        // 延迟跳转到主页面
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        setStatus('error');
        setError(result.error || 'OAuth授权失败');
      }
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
