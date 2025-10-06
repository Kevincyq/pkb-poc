import React, { useState, useRef, useEffect } from 'react';
import styles from './NativeTooltip.module.css';

interface NativeTooltipProps {
  title: React.ReactNode;
  children: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight';
  trigger?: ('hover' | 'click')[];
  maxWidth?: string;
}

export default function NativeTooltip({ 
  title, 
  children, 
  placement = 'bottom',
  trigger = ['hover'],
  maxWidth = '280px'
}: NativeTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  // 处理点击外部关闭
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (tooltipRef.current && !tooltipRef.current.contains(event.target as Node) &&
          triggerRef.current && !triggerRef.current.contains(event.target as Node)) {
        setIsVisible(false);
      }
    }

    if (isVisible && trigger.includes('click')) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isVisible, trigger]);

  // 处理鼠标事件
  const handleMouseEnter = () => {
    if (trigger.includes('hover')) {
      console.log('🎯 Native Tooltip mouse enter');
      setIsVisible(true);
    }
  };

  const handleMouseLeave = () => {
    if (trigger.includes('hover')) {
      console.log('🎯 Native Tooltip mouse leave');
      setIsVisible(false);
    }
  };

  const handleClick = (e: React.MouseEvent) => {
    if (trigger.includes('click')) {
      console.log('🎯 Native Tooltip clicked');
      e.stopPropagation();
      setIsVisible(!isVisible);
    }
  };

  // 计算 Tooltip 位置
  const getTooltipStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      position: 'absolute',
      zIndex: 1200,
      maxWidth,
    };

    switch (placement) {
      case 'top':
        return { ...baseStyle, bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px' };
      case 'topLeft':
        return { ...baseStyle, bottom: '100%', left: '0', marginBottom: '8px' };
      case 'topRight':
        return { ...baseStyle, bottom: '100%', right: '0', marginBottom: '8px' };
      case 'bottom':
        return { ...baseStyle, top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' };
      case 'bottomLeft':
        return { ...baseStyle, top: '100%', left: '0', marginTop: '8px' };
      case 'bottomRight':
        return { ...baseStyle, top: '100%', right: '0', marginTop: '8px' };
      case 'left':
        return { ...baseStyle, right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: '8px' };
      case 'right':
        return { ...baseStyle, left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: '8px' };
      default:
        return { ...baseStyle, top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' };
    }
  };

  return (
    <div className={styles.tooltipContainer}>
      <div
        ref={triggerRef}
        className={styles.trigger}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={styles.tooltip}
          style={getTooltipStyle()}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className={styles.tooltipContent}>
            {title}
          </div>
          <div className={styles.tooltipArrow} />
        </div>
      )}
    </div>
  );
}
