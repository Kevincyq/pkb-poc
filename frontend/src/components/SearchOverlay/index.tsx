import React, { useState, useRef, useEffect } from 'react';
import { Input, List, Typography, Spin, Empty, Tag } from 'antd';
import { SearchOutlined, FileOutlined, CloseOutlined } from '@ant-design/icons';
import api from '../../services/api';
import ErrorBoundary from '../ErrorBoundary';
import './SearchOverlay.css';

const { Text } = Typography;

interface SearchResult {
  content_id: string;
  chunk_id: string;
  title: string;
  text: string;
  modality: string;
  source_uri: string;
  category_name?: string;
  category_color?: string;
  category_confidence?: number;
  score: number;
  created_at: string;
  match_type: string;
}

interface SearchOverlayProps {
  visible: boolean;
  onClose: () => void;
}

export default function SearchOverlay({ visible, onClose }: SearchOverlayProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const inputRef = useRef<any>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // 自动聚焦输入框
  useEffect(() => {
    if (visible && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [visible]);

  // 处理外部点击关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (overlayRef.current && !overlayRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [visible, onClose]);

  // 处理ESC键关闭
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('keydown', handleEscKey);
      return () => {
        document.removeEventListener('keydown', handleEscKey);
      };
    }
  }, [visible, onClose]);

  // 执行搜索
  const performSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setHasSearched(true);

    try {
      const params = new URLSearchParams();
      params.append('q', query.trim());
      params.append('top_k', '10');
      params.append('search_type', 'hybrid');

      console.log('🔍 Performing search with query:', query.trim());
      const response = await api.get(`/search?${params.toString()}`);
      console.log('📊 Search response:', response.data);
      
      const results = response.data.results || [];
      console.log('📋 Search results:', results);
      setSearchResults(results);
    } catch (error: any) {
      console.error('❌ Search error:', error);
      console.error('❌ Error response:', error.response?.data);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 处理搜索输入
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    performSearch(value);
  };

  // 处理回车搜索
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      performSearch(searchQuery);
    }
  };

  // 高亮关键词
  const highlightKeywords = (text: string, keywords: string) => {
    if (!keywords.trim() || !text) return text || '';
    
    try {
      const keywordList = keywords.trim().split(/\s+/);
      let highlightedText = text;
      
      keywordList.forEach(keyword => {
        if (keyword.length > 0) {
          // 转义特殊正则字符
          const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const regex = new RegExp(`(${escapedKeyword})`, 'gi');
          highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
        }
      });
      
      return highlightedText;
    } catch (error) {
      console.error('Error in highlightKeywords:', error);
      return text || '';
    }
  };

  // 获取文件类型图标
  const getFileIcon = (modality: string) => {
    if (modality === 'image') {
      return <FileOutlined style={{ color: '#52c41a' }} />;
    }
    return <FileOutlined style={{ color: '#1890ff' }} />;
  };

  // 处理结果点击
  const handleResultClick = (result: SearchResult) => {
    // 这里可以添加跳转到文档详情的逻辑
    console.log('Clicked result:', result);
    onClose();
  };

  if (!visible) return null;

  return (
    <div className="search-overlay">
      <div className="search-overlay-backdrop" />
      <div className="search-overlay-container" ref={overlayRef}>
        {/* 搜索输入框 */}
        <div className="search-input-container">
          <Input
            ref={inputRef}
            size="large"
            placeholder="搜索知识库内容..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onKeyPress={handleKeyPress}
            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
            suffix={
              <CloseOutlined 
                style={{ color: '#bfbfbf', cursor: 'pointer' }} 
                onClick={onClose}
              />
            }
            style={{
              borderRadius: '8px',
              fontSize: '16px'
            }}
          />
        </div>

        {/* 搜索结果 */}
        <div className="search-results-container">
          {loading ? (
            <div className="search-loading">
              <Spin size="small" />
              <Text type="secondary" style={{ marginLeft: 8 }}>搜索中...</Text>
            </div>
          ) : hasSearched ? (
            searchResults.length > 0 ? (
              <ErrorBoundary fallback={<div style={{ padding: '20px', textAlign: 'center' }}>搜索结果渲染出错</div>}>
                <List
                  dataSource={searchResults}
                  renderItem={(item) => {
                    // 添加安全检查
                    if (!item || typeof item !== 'object') {
                      console.error('Invalid search result item:', item);
                      return null;
                    }

                    return (
                      <ErrorBoundary key={item.chunk_id || item.content_id} fallback={<div>结果项渲染出错</div>}>
                        <List.Item
                          className="search-result-item"
                          onClick={() => handleResultClick(item)}
                        >
                          <div className="search-result-content">
                            <div className="search-result-header">
                              <div className="search-result-title">
                                {getFileIcon(item.modality || '')}
                                <Text 
                                  strong 
                                  dangerouslySetInnerHTML={{
                                    __html: highlightKeywords(item.title || 'Untitled', searchQuery)
                                  }}
                                  style={{ marginLeft: 8 }}
                                />
                              </div>
                              <div className="search-result-categories">
                                {item.category_name && typeof item.category_name === 'string' && (
                                  <Tag 
                                    color={item.category_color || 'blue'}
                                  >
                                    {item.category_name}
                                  </Tag>
                                )}
                                {item.category_confidence && 
                                 typeof item.category_confidence === 'number' && 
                                 !isNaN(item.category_confidence) && 
                                 item.category_confidence > 0 && (
                                  <Tag color="green">
                                    {Math.round(item.category_confidence * 100)}%
                                  </Tag>
                                )}
                              </div>
                            </div>
                            {item.text && typeof item.text === 'string' && item.text.trim() && (
                              <Text 
                                type="secondary" 
                                className="search-result-snippet"
                                dangerouslySetInnerHTML={{
                                  __html: highlightKeywords(
                                    item.text.substring(0, 150) + (item.text.length > 150 ? '...' : ''),
                                    searchQuery
                                  )
                                }}
                              />
                            )}
                          </div>
                        </List.Item>
                      </ErrorBoundary>
                    );
                  }}
                />
              </ErrorBoundary>
            ) : (
              <Empty 
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="没有找到相关内容"
                style={{ padding: '40px 0' }}
              />
            )
          ) : (
            <div className="search-placeholder">
              <Text type="secondary">输入关键词搜索知识库内容</Text>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
