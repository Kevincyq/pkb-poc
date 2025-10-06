import React, { useState, useRef, useEffect } from 'react';
import styles from './NativeDropdown.module.css';

interface MenuItem {
  key: string;
  label: string;
  onClick?: () => void;
}

interface NativeDropdownProps {
  items: MenuItem[];
  trigger: React.ReactNode;
  placement?: 'bottomLeft' | 'bottomRight' | 'topLeft' | 'topRight';
  onMenuClick?: (key: string) => void;
}

export default function NativeDropdown({ 
  items, 
  trigger, 
  placement = 'bottomRight',
  onMenuClick 
}: NativeDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  // 处理点击外部关闭
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // 处理菜单项点击
  const handleMenuItemClick = (item: MenuItem) => {
    console.log('🎯 Native dropdown menu item clicked:', item.key);
    setIsOpen(false);
    item.onClick?.();
    onMenuClick?.(item.key);
  };

  // 处理触发器点击
  const handleTriggerClick = (e: React.MouseEvent) => {
    console.log('🎯 Native dropdown trigger clicked');
    e.stopPropagation(); // 阻止事件冒泡
    setIsOpen(!isOpen);
  };

  // 计算菜单位置
  const getMenuStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      position: 'absolute',
      zIndex: 1000,
    };

    switch (placement) {
      case 'bottomRight':
        return { ...baseStyle, top: '100%', right: 0 };
      case 'bottomLeft':
        return { ...baseStyle, top: '100%', left: 0 };
      case 'topRight':
        return { ...baseStyle, bottom: '100%', right: 0 };
      case 'topLeft':
        return { ...baseStyle, bottom: '100%', left: 0 };
      default:
        return { ...baseStyle, top: '100%', right: 0 };
    }
  };

  return (
    <div className={styles.dropdown} ref={dropdownRef}>
      {/* 触发器 */}
      <div 
        ref={triggerRef}
        className={styles.trigger}
        onClick={handleTriggerClick}
      >
        {trigger}
      </div>

      {/* 下拉菜单 */}
      {isOpen && (
        <div 
          className={styles.menu}
          style={getMenuStyle()}
        >
          {items.map((item) => (
            <div
              key={item.key}
              className={styles.menuItem}
              onClick={() => handleMenuItemClick(item)}
            >
              {item.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
