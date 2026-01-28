import { 
  EllipsisOutlined, 
  PlusOutlined,
  ShoppingOutlined, // 使用ShoppingOutlined替代BriefcaseOutlined
  BookOutlined,
  CoffeeOutlined,
  ThunderboltOutlined,
  BgColorsOutlined,
  FolderOutlined
} from '@ant-design/icons';
import React from 'react';
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

// 系统分类图标和颜色配置（使用Ant Design图标）
const getSystemCategoryConfig = (name: string): { IconComponent: React.ComponentType<any>; bgColor: string; iconColor: string } => {
  const configMap: Record<string, { IconComponent: React.ComponentType<any>; bgColor: string; iconColor: string }> = {
    'Business': {
      IconComponent: ShoppingOutlined, // 购物/商务图标
      bgColor: '#e6f4ff', // 浅蓝色
      iconColor: '#1890ff' // 蓝色
    },
    'Technology': {
      IconComponent: ThunderboltOutlined, // 闪电/科技图标
      bgColor: '#f0e6ff', // 浅紫色
      iconColor: '#722ed1' // 紫色
    },
    'Learning': {
      IconComponent: BookOutlined, // 书本图标
      bgColor: '#f6ffed', // 浅绿色
      iconColor: '#52c41a' // 绿色
    },
    'Life': {
      IconComponent: CoffeeOutlined, // 咖啡杯图标
      bgColor: '#fff7e6', // 浅橙色
      iconColor: '#fa8c16' // 橙色
    },
    'Art': {
      IconComponent: BgColorsOutlined, // 调色板图标
      bgColor: '#fff1f0', // 浅红色
      iconColor: '#ff7875' // 红色
    }
  };
  return configMap[name] || {
    IconComponent: FolderOutlined,
    bgColor: '#f5f5f5',
    iconColor: '#666'
  };
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
          flexDirection: 'column',
          position: 'relative'
        }}
      >
        {/* 左上角图标 - 与系统分类保持一致 */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            left: '16px',
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: '#f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666',
            zIndex: 1
          }}
        >
          <FolderOutlined style={{ fontSize: '24px' }} />
        </div>

        {/* 标题区域 - 包含右上角菜单 */}
        <div className={styles.customCardTitle} style={{ position: 'relative', minHeight: '72px' }}>
          <span 
            className={styles.titleText} 
            style={{ 
              cursor: 'pointer',
              marginLeft: '64px',
              display: 'block'
            }}
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
                  padding: '4px',
                  position: 'absolute',
                  top: '12px',
                  right: '16px',
                  zIndex: 2
                }}
              />
            }
          />
        </div>

        {/* 中部区域 - 与系统分类保持一致的结构 */}
        <div 
          className={styles.systemIconArea}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            paddingTop: '60px', /* 为左上角图标留出空间 */
            paddingBottom: '40px', /* 为底部内容数量留出空间 */
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' /* 保留渐变背景 */
          }}
          onClick={(e) => {
            console.log('🎯 Icon area clicked, triggering navigation');
            onClick?.();
          }}
        >
        </div>

        {/* 底部信息 */}
        <div 
          className={styles.cardFooter}
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
  const categoryConfig = getSystemCategoryConfig(title);
  
  return (
    <div 
      onClick={onClick}
      className={styles.collectionCard}
      style={{
        minHeight: '220px',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative'
      }}
    >
      {/* 左上角图标 */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '16px',
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          backgroundColor: categoryConfig.bgColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: categoryConfig.iconColor,
          zIndex: 1
        }}
      >
        <categoryConfig.IconComponent style={{ fontSize: '24px' }} />
      </div>

      {/* 中部区域 - 分类名字居中显示 */}
      <div 
        className={styles.systemIconArea}
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          paddingTop: '60px', /* 为左上角图标留出空间 */
          paddingBottom: '40px' /* 为底部内容数量留出空间 */
        }}
      >
        <span className={styles.titleText} style={{ 
          fontSize: '18px',
          textAlign: 'center',
          fontWeight: 500,
          color: '#1f1f1f'
        }}>
          {title}
        </span>
      </div>

      {/* 底部信息 */}
      <div className={styles.cardFooter}>
        {contentCount}条内容
      </div>
    </div>
  );
}