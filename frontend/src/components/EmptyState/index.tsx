import { SearchOutlined } from '@ant-design/icons';

interface EmptyStateProps {
  type: 'noResult' | 'searching';
}

export default function EmptyState({ type }: EmptyStateProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 0'
    }}>
      <SearchOutlined style={{ 
        fontSize: '48px', 
        color: '#d9d9d9',
        marginBottom: '16px'
      }} />
      <p style={{ 
        color: '#999', 
        fontSize: '14px',
        margin: 0
      }}>
        {type === 'noResult' 
          ? '请尝试其他关键词，或者尝试其他关键词' 
          : '正在搜索相关内容...'}
      </p>
    </div>
  );
}
