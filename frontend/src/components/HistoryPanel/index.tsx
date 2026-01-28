/**
 * 任务历史面板组件
 * 显示最近5条聊天与任务历史
 */

import { useEffect, useState } from 'react';
import { Empty } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import qaService from '../../services/qaService';
import type { QAHistoryItem } from '../../types/qa';
import styles from './HistoryPanel.module.css';

interface HistoryPanelProps {
  onQuestionClick?: (question: string) => void;
}

export default function HistoryPanel({ onQuestionClick }: HistoryPanelProps) {
  const [history, setHistory] = useState<QAHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await qaService.getHistory(undefined, 3); // 只获取最近3条记录
      setHistory(response.history || []);
    } catch (error) {
      console.error('Failed to load history:', error);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  // 如果没有历史记录，不显示
  if (!loading && history.length === 0) {
    return null;
  }

  const handleItemClick = (item: QAHistoryItem) => {
    onQuestionClick?.(item.question);
  };

  return (
    <div className={styles.historyPanel}>
      <div className={styles.header}>
        <MessageOutlined className={styles.headerIcon} />
        <span className={styles.headerTitle}>History</span>
      </div>
      
      {loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : (
        <div className={styles.historyGrid}>
          {history.map((item) => (
            <div
              key={item.id}
              className={styles.historyItem}
              onClick={() => handleItemClick(item)}
            >
              <div className={styles.itemIcon}>
                <MessageOutlined />
              </div>
              <div className={styles.itemContent}>
                <div className={styles.itemTitle}>{item.question}</div>
                <div className={styles.itemSnippet}>
                  {item.answer && item.answer.length > 60 
                    ? item.answer.substring(0, 60) + '...'
                    : item.answer}
                </div>
                <div className={styles.itemDate}>
                  {new Date(item.created_at).toLocaleDateString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

