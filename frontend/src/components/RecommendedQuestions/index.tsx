/**
 * 推荐问题面板组件
 * 显示知识库系统推荐的问题
 */

import { useEffect, useState } from 'react';
import { Empty } from 'antd';
import { BulbOutlined } from '@ant-design/icons';
import api from '../../services/api';
import styles from './RecommendedQuestions.module.css';

interface RecommendedQuestion {
  id: string;
  question: string;
  content_id?: string; // 关联的内容ID（如果有）
}

interface RecommendedQuestionsProps {
  onQuestionClick?: (question: string) => void;
}

export default function RecommendedQuestions({ onQuestionClick }: RecommendedQuestionsProps) {
  const [questions, setQuestions] = useState<RecommendedQuestion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecommendedQuestions();
  }, []);

  const loadRecommendedQuestions = async () => {
    try {
      setLoading(true);
      // 调用推荐问题API
      const response = await api.get<{ questions: RecommendedQuestion[] }>('/qa/recommended-questions');
      setQuestions(response.data.questions || []);
    } catch (error) {
      console.error('Failed to load recommended questions:', error);
      setQuestions([]);
    } finally {
      setLoading(false);
    }
  };

  // 如果没有推荐问题，不显示
  if (!loading && questions.length === 0) {
    return null;
  }

  const handleQuestionClick = (question: RecommendedQuestion) => {
    onQuestionClick?.(question.question);
  };

  return (
    <div className={styles.recommendedPanel}>
      <div className={styles.header}>
        <BulbOutlined className={styles.headerIcon} />
        <span className={styles.headerTitle}>Suggestions</span>
      </div>
      
      {loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : (
        <div className={styles.questionsList}>
          {questions.map((question) => (
            <div
              key={question.id}
              className={styles.questionItem}
              onClick={() => handleQuestionClick(question)}
            >
              <BulbOutlined className={styles.questionIcon} />
              <span className={styles.questionText}>{question.question}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

