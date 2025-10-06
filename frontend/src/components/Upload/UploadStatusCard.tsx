import React from 'react';
import { Card, Progress, Tag, Button, Typography, Space } from 'antd';
import { 
  FileOutlined, 
  LoadingOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  EyeOutlined 
} from '@ant-design/icons';
import styles from './UploadStatusCard.module.css';

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
        return file.uploadProgress ? `上传中 ${file.uploadProgress}%` : '正在上传...';
      case 'parsing':
        return '解析文档内容中...';
      case 'classifying':
        // 根据进度显示更具体的分类阶段
        if (file.progress && file.progress >= 85) {
          return 'AI精准分类中...';
        } else if (file.progress && file.progress >= 60) {
          return '智能分类中...';
        } else {
          return '准备分类中...';
        }
      case 'completed':
        return '✅ 处理完成';
      case 'error':
        return '❌ 处理失败';
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

  const getEstimatedTimeRemaining = () => {
    if (file.status === 'completed' || file.status === 'error') return null;
    
    const progress = file.status === 'uploading' ? (file.uploadProgress || 0) : (file.progress || 0);
    if (progress <= 0) return null;
    
    const elapsed = Date.now() - file.startTime;
    const totalEstimated = (elapsed / progress) * 100;
    const remaining = Math.max(0, totalEstimated - elapsed);
    
    const remainingSeconds = Math.floor(remaining / 1000);
    if (remainingSeconds < 60) return `约${remainingSeconds}秒`;
    const remainingMinutes = Math.floor(remainingSeconds / 60);
    return `约${remainingMinutes}分钟`;
  };

  return (
    <Card 
      size="small" 
      className={styles.uploadCard}
      style={{ 
        border: file.status === 'error' ? '1px solid #ff4d4f' : undefined
      }}
    >
      <div className={styles.uploadContent}>
        {/* 文件图标 */}
        <div className={styles.uploadIcon}>
          {getStatusIcon()}
        </div>

        {/* 文件信息 */}
        <div className={styles.uploadInfo}>
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
            {getEstimatedTimeRemaining() && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                剩余{getEstimatedTimeRemaining()}
              </Text>
            )}
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
              showInfo={true}
              format={(percent) => {
                if (file.status === 'uploading') {
                  return `${percent}%`;
                } else if (file.status === 'parsing') {
                  return '解析中';
                } else if (file.status === 'classifying') {
                  if (percent && percent >= 85) {
                    return 'AI分类';
                  } else if (percent && percent >= 60) {
                    return '智能分类';
                  } else {
                    return '准备中';
                  }
                }
                return `${percent}%`;
              }}
              style={{ 
                marginBottom: 8,
                transition: 'all 0.3s ease'
              }}
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
                    color={category.color || 'blue'}
                    style={{ cursor: 'pointer' }}
                    onClick={() => onViewCollection?.(category.name)}
                  >
                    {category.name} ({Math.round(category.confidence * 100)}%)
                    {category.role === 'user_rule' && ' 📁'}
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
