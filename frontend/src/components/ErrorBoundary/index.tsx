import React, { Component, ReactNode } from 'react';
import { Alert } from 'antd';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 记录错误信息
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // 这里可以将错误上报给错误监控服务
    // logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义的 fallback UI，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认的错误 UI
      return (
        <div style={{ padding: '20px' }}>
          <Alert
            message="组件渲染错误"
            description="抱歉，这个组件遇到了一些问题。请刷新页面重试。"
            type="error"
            showIcon
            action={
              <button 
                onClick={() => window.location.reload()}
                style={{
                  padding: '4px 8px',
                  border: '1px solid #ff4d4f',
                  borderRadius: '4px',
                  background: 'white',
                  color: '#ff4d4f',
                  cursor: 'pointer'
                }}
              >
                刷新页面
              </button>
            }
          />
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
