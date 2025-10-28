import React, { useState } from 'react';
import { Form, Input, Button, message, Card, Typography, Space, Divider } from 'antd';
import { UserOutlined, LockOutlined, GoogleOutlined } from '@ant-design/icons';
import { useAuth } from '../../stores/AuthContext';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  // Process form submission
  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  // 处理Google登录
  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      await loginWithGoogle();
      // Google OAuth会重定向到Google页面，这里不需要额外处理
    } catch (error: any) {
      message.error(error.message || 'Google登录失败');
      setGoogleLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="login-card-wrapper">
          <Card className="login-card" bordered={false}>
            <div className="login-header">
              <Title level={2} className="login-title">
                登录您的AI个人知识助理
              </Title>
            </div>

            <Form
              form={form}
              name="login"
              onFinish={handleSubmit}
              autoComplete="off"
              size="large"
              className="login-form"
            >
              <Form.Item
                name="username"
                rules={[
                  { required: true, message: '请输入您的账号' },
                  { min: 1, message: '账号不能为空' }
                ]}
              >
                <Input
                  prefix={<UserOutlined className="input-icon" />}
                  placeholder="输入您的账号"
                  className="login-input"
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入您的密码' },
                  { min: 1, message: '密码不能为空' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined className="input-icon" />}
                  placeholder="输入您的密码"
                  className="login-input"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  className="login-button"
                  block
                >
                  登录
                </Button>
              </Form.Item>
            </Form>

            <Divider className="login-divider">
              <Text type="secondary">或</Text>
            </Divider>

            <Button
              type="default"
              icon={<GoogleOutlined style={{ color: '#4285F4' }} />}
              onClick={handleGoogleLogin}
              loading={googleLoading}
              className="google-login-button"
              block
            >
              Google账户登录
            </Button>

            <div className="login-footer">
              <Space split={<Divider type="vertical" />}>
                <Text type="secondary" className="footer-text">
                  测试账号: test / test
                </Text>
              </Space>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
