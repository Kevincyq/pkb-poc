import { EllipsisOutlined, PlusOutlined } from '@ant-design/icons';
import { Dropdown, type MenuProps } from 'antd';

interface CollectionCardProps {
  title: string;
  contentCount: number;
  isCreateCard?: boolean;
  isCustomCollection?: boolean;
  onDelete?: () => void;
  onRename?: () => void;
  onClick?: () => void;
}

const getCollectionImage = (name: string) => {
  const imageMap: Record<string, string> = {
    '职场商务': '/images/collections/business.jpg',
    '学习成长': '/images/collections/study.jpg',
    '生活点滴': '/images/collections/life.jpg',
    '科技前沿': '/images/collections/tech.jpg'
  };
  return imageMap[name] || '/images/collections/default.jpg';
};

export default function CollectionCard({ 
  title, 
  contentCount,
  isCreateCard = false,
  isCustomCollection = false,
  onDelete,
  onRename,
  onClick 
}: CollectionCardProps) {
  // 自建合集的下拉菜单选项
  const menuItems: MenuProps['items'] = [
    {
      key: 'rename',
      label: '重命名',
      onClick: () => {
        onRename?.();
      }
    },
    {
      key: 'delete',
      label: '删除',
      onClick: () => {
        if (onDelete) {
          onDelete();
        }
      }
    }
  ];

  if (isCreateCard) {
    return (
      <div 
        onClick={onClick}
        style={{
          width: '100%',
          height: '100%',
          border: '1px dashed #d9d9d9',
          borderRadius: '8px',
          overflow: 'hidden',
          cursor: 'pointer',
          background: '#f5f5f5',
          transition: 'all 0.2s',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '220px'
        }}
      >
        <PlusOutlined style={{ 
          fontSize: '24px',
          color: '#bfbfbf'
        }} />
      </div>
    );
  }

  // 自建合集卡片
  if (isCustomCollection) {
    return (
      <div style={{
        width: '100%',
        border: '1px solid #e5e5e5',
        borderRadius: '8px',
        overflow: 'hidden',
        background: '#fff',
        transition: 'all 0.2s',
        minHeight: '220px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* 标题区域 */}
        <div style={{
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{
            fontSize: '14px',
            fontWeight: '500',
            color: '#1f1f1f',
            lineHeight: '20px',
            cursor: 'pointer'
          }} onClick={onClick}>
            {title}
          </span>
          <Dropdown 
            menu={{ items: menuItems }} 
            trigger={['click']}
            placement="bottomRight"
          >
            <EllipsisOutlined style={{ 
              fontSize: '16px',
              color: '#999',
              padding: '4px',
              cursor: 'pointer'
            }} />
          </Dropdown>
        </div>

        {/* 简洁的图标区域 */}
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#fff',
          fontSize: '32px',
          padding: '40px 0'
        }}>
          📁
        </div>

        {/* 底部信息 */}
        <div style={{
          padding: '12px 16px',
          fontSize: '12px',
          color: '#666',
          lineHeight: '18px',
          borderTop: '1px solid #f0f0f0'
        }}>
          {contentCount}条内容
        </div>
      </div>
    );
  }

  // 系统默认合集卡片
  return (
    <div 
      onClick={onClick}
      style={{
        width: '100%',
        border: '1px solid #e5e5e5',
        borderRadius: '8px',
        overflow: 'hidden',
        cursor: 'pointer',
        background: '#fff',
        transition: 'all 0.2s'
      }}
    >
      {/* 标题区域 */}
      <div style={{
        padding: '12px 16px 8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{
          fontSize: '14px',
          fontWeight: '500',
          color: '#1f1f1f',
          lineHeight: '20px'
        }}>
          {title}
        </span>
      </div>

      {/* 图片区域 */}
      <div style={{
        width: '100%',
        height: '140px',
        overflow: 'hidden'
      }}>
        <img 
          src={getCollectionImage(title)}
          alt={title}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
        />
      </div>

      {/* 底部信息 */}
      <div style={{
        padding: '8px 16px',
        fontSize: '12px',
        color: '#666',
        lineHeight: '18px'
      }}>
        {contentCount}条内容
      </div>
    </div>
  );
}