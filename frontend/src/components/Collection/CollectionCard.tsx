import { EllipsisOutlined, PlusOutlined } from '@ant-design/icons';
import NativeDropdown from '../NativeDropdown';
import styles from './CollectionCard.module.css';

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
  const menuItems = [
    {
      key: 'rename',
      label: '重命名'
    },
    {
      key: 'delete',
      label: '删除',
      danger: true
    }
  ];

  if (isCreateCard) {
    return (
      <div 
        onClick={onClick}
        className={styles.createCard}
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
      <div 
        className={styles.collectionCard} 
        style={{
          minHeight: '220px',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* 标题区域 */}
        <div className={styles.customCardTitle}>
          <span 
            className={styles.titleText} 
            style={{ cursor: 'pointer' }}
            onClick={() => {
              console.log('🎯 Title clicked, triggering navigation');
              onClick?.();
            }}
          >
            {title}
          </span>
          <NativeDropdown
            items={menuItems}
            placement="bottomRight"
            onMenuClick={(key) => {
              if (key === 'rename') {
                onRename?.();
              } else if (key === 'delete') {
                onDelete?.();
              }
            }}
            trigger={
              <EllipsisOutlined 
                data-testid="collection-more-button"
                style={{ 
                  fontSize: '16px',
                  color: '#999',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              />
            }
          />
        </div>

        {/* 简洁的图标区域 */}
        <div 
          className={styles.customIconArea}
          style={{ cursor: 'pointer' }}
          onClick={(e) => {
            console.log('🎯 Icon area clicked, triggering navigation');
            onClick?.();
          }}
        >
          📁
        </div>

        {/* 底部信息 */}
        <div 
          className={styles.customCardFooter}
          style={{ cursor: 'pointer' }}
          onClick={(e) => {
            console.log('🎯 Footer area clicked, triggering navigation');
            onClick?.();
          }}
        >
          {contentCount}条内容
        </div>
      </div>
    );
  }

  // 系统默认合集卡片
  return (
    <div 
      onClick={onClick}
      className={styles.collectionCard}
    >
      {/* 标题区域 */}
      <div className={styles.cardTitle}>
        <span className={styles.titleText}>
          {title}
        </span>
      </div>

      {/* 图片区域 */}
      <div className={styles.imageArea}>
        <img 
          src={getCollectionImage(title)}
          alt={title}
          className={styles.cardImage}
        />
      </div>

      {/* 底部信息 */}
      <div className={styles.cardFooter}>
        {contentCount}条内容
      </div>
    </div>
  );
}