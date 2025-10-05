import React from 'react';

interface SafeMarkdownRendererProps {
  content: string;
  className?: string;
}

const SafeMarkdownRenderer: React.FC<SafeMarkdownRendererProps> = ({ 
  content, 
  className 
}) => {
  if (!content || typeof content !== 'string') {
    return <div className={className}>无内容</div>;
  }

  try {
    // 按行分割处理
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let listItems: React.ReactNode[] = [];
    let inList = false;

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      
      // 空行
      if (trimmed === '') {
        if (inList) {
          elements.push(<ul key={`list-${index}`}>{listItems}</ul>);
          listItems = [];
          inList = false;
        }
        elements.push(<br key={`br-${index}`} />);
        return;
      }
      
      // 标题
      if (trimmed.startsWith('### ')) {
        if (inList) {
          elements.push(<ul key={`list-${index}`}>{listItems}</ul>);
          listItems = [];
          inList = false;
        }
        elements.push(<h3 key={`h3-${index}`}>{trimmed.substring(4)}</h3>);
        return;
      }
      
      if (trimmed.startsWith('## ')) {
        if (inList) {
          elements.push(<ul key={`list-${index}`}>{listItems}</ul>);
          listItems = [];
          inList = false;
        }
        elements.push(<h2 key={`h2-${index}`}>{trimmed.substring(3)}</h2>);
        return;
      }
      
      if (trimmed.startsWith('# ')) {
        if (inList) {
          elements.push(<ul key={`list-${index}`}>{listItems}</ul>);
          listItems = [];
          inList = false;
        }
        elements.push(<h1 key={`h1-${index}`}>{trimmed.substring(2)}</h1>);
        return;
      }
      
      // 列表项
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const listContent = renderInlineFormatting(trimmed.substring(2));
        listItems.push(<li key={`li-${index}`}>{listContent}</li>);
        inList = true;
        return;
      }
      
      // 普通段落
      if (inList) {
        elements.push(<ul key={`list-${index}`}>{listItems}</ul>);
        listItems = [];
        inList = false;
      }
      
      const formattedContent = renderInlineFormatting(trimmed);
      elements.push(<p key={`p-${index}`}>{formattedContent}</p>);
    });
    
    // 关闭未关闭的列表
    if (inList) {
      elements.push(<ul key="final-list">{listItems}</ul>);
    }
    
    return (
      <div 
        className={className}
        style={{
          lineHeight: '1.6',
          color: '#333'
        }}
      >
        {elements}
      </div>
    );
  } catch (error) {
    console.error('Error in SafeMarkdownRenderer:', error);
    return (
      <div className={className} style={{ color: '#999' }}>
        内容渲染出错
      </div>
    );
  }
};

// 处理行内格式（粗体、链接等）
const renderInlineFormatting = (text: string): React.ReactNode[] => {
  const elements: React.ReactNode[] = [];
  let currentIndex = 0;
  
  // 处理粗体 **text**
  const boldRegex = /\*\*(.*?)\*\*/g;
  let match;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // 添加粗体前的文本
    if (match.index > currentIndex) {
      elements.push(text.substring(currentIndex, match.index));
    }
    
    // 添加粗体文本
    elements.push(<strong key={`bold-${match.index}`}>{match[1]}</strong>);
    currentIndex = match.index + match[0].length;
  }
  
  // 添加剩余文本
  if (currentIndex < text.length) {
    elements.push(text.substring(currentIndex));
  }
  
  // 如果没有找到任何格式，返回原文本
  if (elements.length === 0) {
    return [text];
  }
  
  return elements;
};

export default SafeMarkdownRenderer;
