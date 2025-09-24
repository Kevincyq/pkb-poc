import React from 'react';
import { Card, Progress, Tag, Button, Typography, Space } from 'antd';
import { 
  FileOutlined, 
  LoadingOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  EyeOutlined 
} from '@ant-design/icons';

const { Text } = Typography;

export interface UploadFileStatus {
  id: string;
  fileName: string;
  fileSize: number;
  status: 'uploading' | 'parsing' | 'classifying' | 'completed' | 'error';
  progress: number;
  uploadProgress?: number;
  contentId?: string;
  categories?: Array<{
    id: string;
    name: string;
    confidence: number;
  }>;
  errorMessage?: string;
  startTime: number;
}

interface UploadStatusCardProps {
  file: UploadFileStatus;
  onViewCollection?: (categoryName: string) => void;
  onRetry?: (fileId: string) => void;
  onRemove?: (fileId: string) => void;
}

const UploadStatusCard: React.FC<UploadStatusCardProps> = ({
  file,
  onViewCollection,
  onRetry,
  onRemove
}) => {
  const getStatusIcon = () => {
    switch (file.status) {
      case 'uploading':
      case 'parsing':
      case 'classifying':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <FileOutlined />;
    }
  };

  const getStatusText = () => {
    switch (file.status) {
      case 'uploading':
        return '正在上传...';
      case 'parsing':
        return '正在解析文件内容...';
      case 'classifying':
        return '正在AI智能分类...';
      case 'completed':
        return '处理完成';
      case 'error':
        return '处理失败';
      default:
        return '等待处理';
    }
  };

  const getStatusColor = () => {
    switch (file.status) {
      case 'uploading':
      case 'parsing':
      case 'classifying':
        return 'processing';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getElapsedTime = () => {
    const elapsed = Date.now() - file.startTime;
    const seconds = Math.floor(elapsed / 1000);
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}分${seconds % 60}秒`;
  };

  return (
    <Card 
      size="small" 
      style={{ 
        marginBottom: 12,
        border: file.status === 'error' ? '1px solid #ff4d4f' : undefined
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        {/* 文件图标 */}
        <div style={{ fontSize: 24, marginTop: 4 }}>
          {getStatusIcon()}
        </div>

        {/* 文件信息 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 文件名和大小 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Text strong style={{ fontSize: 14 }} ellipsis={{ tooltip: file.fileName }}>
              {file.fileName}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {formatFileSize(file.fileSize)}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {getElapsedTime()}
            </Text>
          </div>

          {/* 状态标签 */}
          <div style={{ marginBottom: 8 }}>
            <Tag color={getStatusColor()}>{getStatusText()}</Tag>
          </div>

          {/* 进度条 */}
          {(file.status === 'uploading' || file.status === 'parsing' || file.status === 'classifying') && (
            <Progress
              percent={file.status === 'uploading' ? (file.uploadProgress || 0) : file.progress}
              size="small"
              status="active"
              showInfo={false}
              style={{ marginBottom: 8 }}
            />
          )}

          {/* 分类结果 */}
          {file.status === 'completed' && file.categories && file.categories.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 12, marginRight: 8 }}>
                已分类到:
              </Text>
              <Space wrap>
                {file.categories.map((category) => (
                  <Tag 
                    key={category.id} 
                    color="blue" 
                    style={{ cursor: 'pointer' }}
                    onClick={() => onViewCollection?.(category.name)}
                  >
                    {category.name} ({Math.round(category.confidence * 100)}%)
                  </Tag>
                ))}
              </Space>
            </div>
          )}

          {/* 错误信息 */}
          {file.status === 'error' && file.errorMessage && (
            <div style={{ marginBottom: 8 }}>
              <Text type="danger" style={{ fontSize: 12 }}>
                {file.errorMessage}
              </Text>
            </div>
          )}

          {/* 操作按钮 */}
          {file.status === 'completed' && file.categories && file.categories.length > 0 && (
            <div>
              <Space>
                <Button 
                  type="link" 
                  size="small" 
                  icon={<EyeOutlined />}
                  onClick={() => onViewCollection?.(file.categories![0].name)}
                >
                  查看合集
                </Button>
                <Button 
                  type="link" 
                  size="small" 
                  onClick={() => onRemove?.(file.id)}
                >
                  移除
                </Button>
              </Space>
            </div>
          )}

          {file.status === 'error' && (
            <div>
              <Space>
                <Button 
                  type="link" 
                  size="small" 
                  onClick={() => onRetry?.(file.id)}
                >
                  重试
                </Button>
                <Button 
                  type="link" 
                  size="small" 
                  onClick={() => onRemove?.(file.id)}
                >
                  移除
                </Button>
              </Space>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default UploadStatusCard;
