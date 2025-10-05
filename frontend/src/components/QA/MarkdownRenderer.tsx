/**
 * 简单的Markdown渲染器
 * 支持基本的Markdown语法和内部链接
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import SafeMarkdownRenderer from './SafeMarkdownRenderer';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const navigate = useNavigate();

  // 处理内部链接点击
  const handleLinkClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'A') {
      e.preventDefault();
      const href = target.getAttribute('href');
      if (href?.startsWith('#/')) {
        // 处理内部链接
        const path = href.substring(1); // 移除 #
        navigate(path);
      } else if (href?.startsWith('http')) {
        // 处理外部链接
        window.open(href, '_blank');
      }
    }
  };

  // 简单的Markdown转HTML
  const renderMarkdown = (text: string): string => {
    if (!text || typeof text !== 'string') {
      return '';
    }
    
    try {
      // 按行分割处理
      const lines = text.split('\n');
      const processedLines: string[] = [];
      let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];
      const trimmed = line.trim();
      
      // 空行
      if (trimmed === '') {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        processedLines.push('<br>');
        continue;
      }
      
      // 标题
      if (trimmed.startsWith('### ')) {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        processedLines.push(`<h3>${trimmed.substring(4)}</h3>`);
        continue;
      }
      
      if (trimmed.startsWith('## ')) {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        processedLines.push(`<h2>${trimmed.substring(3)}</h2>`);
        continue;
      }
      
      if (trimmed.startsWith('# ')) {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        processedLines.push(`<h1>${trimmed.substring(2)}</h1>`);
        continue;
      }
      
      // 列表项
      if (trimmed.startsWith('- ') || /^\d+\.\s/.test(trimmed)) {
        if (!inList) {
          processedLines.push('<ul>');
          inList = true;
        }
        const content = trimmed.startsWith('- ') 
          ? trimmed.substring(2) 
          : trimmed.replace(/^\d+\.\s/, '');
        
        // 处理列表项中的格式
        const formattedContent = content
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        
        processedLines.push(`<li>${formattedContent}</li>`);
        continue;
      }
      
      // 普通段落
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      
      // 处理段落中的格式
      const formattedLine = trimmed
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
      
      processedLines.push(`<p>${formattedLine}</p>`);
    }
    
      // 关闭未关闭的列表
      if (inList) {
        processedLines.push('</ul>');
      }
      
      return processedLines.join('');
    } catch (error) {
      console.error('Error in renderMarkdown:', error);
      return '';
    }
  };

  return (
    <div onClick={handleLinkClick}>
      <SafeMarkdownRenderer content={content} className={className} />
    </div>
  );
}
