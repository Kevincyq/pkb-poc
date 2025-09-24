/**
 * 问答助理状态管理Hook
 */
import { useState, useCallback, useRef } from 'react';
import type { QAMessage } from '../types/qa';

export interface QAAssistantState {
  visible: boolean;
  initialQuestion: string;
  messages: QAMessage[];
  isLoading: boolean;
  error: string | null;
}

export interface QAAssistantActions {
  show: (initialQuestion?: string) => void;
  hide: () => void;
  toggle: () => void;
  setInitialQuestion: (question: string) => void;
  clearError: () => void;
}

/**
 * 问答助理Hook - 管理问答助理的显示状态和交互
 */
export function useQAAssistant(): QAAssistantState & QAAssistantActions {
  const [visible, setVisible] = useState(false);
  const [initialQuestion, setInitialQuestionState] = useState('');
  const [messages, setMessages] = useState<QAMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialQuestionRef = useRef<string>('');

  // 显示问答助理
  const show = useCallback((question?: string) => {
    if (question) {
      setInitialQuestionState(question);
      initialQuestionRef.current = question;
    }
    setVisible(true);
    setError(null);
  }, []);

  // 隐藏问答助理
  const hide = useCallback(() => {
    setVisible(false);
    // 清空初始问题，避免下次打开时重复发送
    setTimeout(() => {
      setInitialQuestionState('');
      initialQuestionRef.current = '';
    }, 300);
  }, []);

  // 切换显示状态
  const toggle = useCallback(() => {
    if (visible) {
      hide();
    } else {
      show();
    }
  }, [visible, show, hide]);

  // 设置初始问题
  const setInitialQuestion = useCallback((question: string) => {
    setInitialQuestionState(question);
    initialQuestionRef.current = question;
  }, []);

  // 清除错误
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // 状态
    visible,
    initialQuestion,
    messages,
    isLoading,
    error,
    
    // 操作
    show,
    hide,
    toggle,
    setInitialQuestion,
    clearError
  };
}

export default useQAAssistant;
