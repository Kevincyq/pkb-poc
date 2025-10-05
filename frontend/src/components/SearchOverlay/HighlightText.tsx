import React from 'react';

interface HighlightTextProps {
  text: string;
  searchQuery: string;
  className?: string;
  style?: React.CSSProperties;
}

const HighlightText: React.FC<HighlightTextProps> = ({ 
  text, 
  searchQuery, 
  className,
  style 
}) => {
  // 如果没有搜索查询或文本，直接返回原文本
  if (!searchQuery || !text) {
    return <span className={className} style={style}>{text}</span>;
  }

  try {
    // 分割搜索关键词
    const keywords = searchQuery.trim().split(/\s+/).filter(k => k.length > 0);
    
    if (keywords.length === 0) {
      return <span className={className} style={style}>{text}</span>;
    }

    // 创建正则表达式，转义特殊字符
    const escapedKeywords = keywords.map(keyword => 
      keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    );
    
    const regex = new RegExp(`(${escapedKeywords.join('|')})`, 'gi');
    
    // 分割文本
    const parts = text.split(regex);
    
    return (
      <span className={className} style={style}>
        {parts.map((part, index) => {
          // 检查这个部分是否匹配关键词
          const isHighlight = keywords.some(keyword => 
            part.toLowerCase() === keyword.toLowerCase()
          );
          
          if (isHighlight) {
            return (
              <mark 
                key={index}
                style={{
                  backgroundColor: '#fffb8f',
                  padding: '1px 2px',
                  borderRadius: '3px'
                }}
              >
                {part}
              </mark>
            );
          }
          
          return <span key={index}>{part}</span>;
        })}
      </span>
    );
  } catch (error) {
    console.error('Error in HighlightText:', error);
    // 出错时返回原文本
    return <span className={className} style={style}>{text}</span>;
  }
};

export default HighlightText;
