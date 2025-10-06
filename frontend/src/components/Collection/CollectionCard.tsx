import { EllipsisOutlined, PlusOutlined } from '@ant-design/icons';
import { Dropdown, type MenuProps } from 'antd';
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
      <div className={styles.collectionCard} style={{
        minHeight: '220px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* 标题区域 */}
        <div className={styles.customCardTitle}>
          <span className={styles.titleText} style={{
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
        <div className={styles.customIconArea}>
          📁
        </div>

        {/* 底部信息 */}
        <div className={styles.customCardFooter}>
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