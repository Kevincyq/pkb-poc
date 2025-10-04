/**
 * 问答助理浮层组件
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  CloseOutlined, 
  ExpandOutlined,
  CompressOutlined,
  RobotOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { message } from 'antd';
import styles from './QAAssistant.module.css';
import { useTypewriter } from '../../hooks/useTypewriter';
import qaService from '../../services/qaService';
import type { QAMessage, QAResponse } from '../../types/qa';
import MarkdownRenderer from './MarkdownRenderer';

interface QAAssistantProps {
  visible: boolean;
  onClose: () => void;
  initialQuestion?: string; // 初始问题（从输入框传入）
}

export default function QAAssistant({ 
  visible, 
  onClose, 
  initialQuestion 
}: QAAssistantProps) {
  const [messages, setMessages] = useState<QAMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const currentAssistantMessageRef = useRef<QAMessage | null>(null);
  const processedInitialQuestionRef = useRef<string>(''); // 记录已处理的初始问题

  // 打字机效果
  const typewriter = useTypewriter(
    currentAssistantMessageRef.current?.content || '',
    {
      speed: 50,
      onComplete: () => {
        // 打字机完成后，更新消息状态
        if (currentAssistantMessageRef.current) {
          setMessages(prev => prev.map(msg => 
            msg.id === currentAssistantMessageRef.current?.id 
              ? { ...msg, isTyping: false }
              : msg
          ));
          currentAssistantMessageRef.current = null;
        }
      }
    }
  );

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, []);

  // 发送消息（只接收外部传入的问题）
  const handleSendMessage = useCallback(async (question: string) => {
    const messageText = question.trim();
    if (!messageText || isLoading) return;

    setError(null);

    // 添加用户消息
    const userMessage: QAMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // 调用问答API
      console.log('🚀 开始调用问答API，问题:', messageText);
      const response: QAResponse = await qaService.askQuestion(messageText);
      console.log('✅ 成功收到API响应:', response);

      // 添加AI回答消息（初始为空，准备打字机效果）
      const assistantMessage: QAMessage = {
        id: `assistant_${Date.now()}`,
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        isTyping: true,
        sources: response.sources || []  // 包含相关文档来源
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // 设置当前打字机消息并开始打字机效果
      currentAssistantMessageRef.current = assistantMessage;
      setTimeout(() => {
        typewriter.start();
      }, 300); // 稍微延迟开始打字机效果

    } catch (err: any) {
      console.error('❌ QA request failed:', err);
      console.error('❌ Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        stack: err.stack
      });
      const errorMessage = err.message || '问答服务暂时不可用，请稍后重试';
      setError(errorMessage);
      message.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, typewriter]);

  // 初始化会话（不加载历史记录）
  const initializeSession = useCallback(async () => {
    if (isInitialized) return;
    
    try {
      // 创建新的会话ID，不加载历史记录
      qaService.createNewSession();
      setMessages([]); // 每次都是空的消息列表
      setIsInitialized(true);
    } catch (err) {
      console.error('Failed to initialize QA session:', err);
      setError('初始化会话失败');
      setIsInitialized(true);
    }
  }, [isInitialized]);

  // 切换全屏模式
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev);
  }, []);

  // 当组件可见时初始化
  useEffect(() => {
    if (visible && !isInitialized) {
      initializeSession();
    }
  }, [visible, isInitialized, initializeSession]);

  // 当会话初始化完成且有初始问题时，自动发送（只发送一次）
  useEffect(() => {
    if (isInitialized && initialQuestion && initialQuestion.trim()) {
      const currentQuestion = initialQuestion.trim();
      // 检查是否已经处理过这个问题
      if (processedInitialQuestionRef.current !== currentQuestion) {
        processedInitialQuestionRef.current = currentQuestion;
        const timer = setTimeout(() => {
          handleSendMessage(currentQuestion);
        }, 500);
        return () => clearTimeout(timer);
      }
    }
  }, [isInitialized, initialQuestion, handleSendMessage]);

  // 当消息更新时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 当打字机文本更新时，更新对应的消息内容
  useEffect(() => {
    if (currentAssistantMessageRef.current && typewriter.displayText) {
      setMessages(prev => prev.map(msg => 
        msg.id === currentAssistantMessageRef.current?.id 
          ? { ...msg, content: typewriter.displayText }
          : msg
      ));
    }
  }, [typewriter.displayText]);

  // 当组件关闭时重置状态
  useEffect(() => {
    if (!visible) {
      setIsFullscreen(false);
      setMessages([]);
      setIsInitialized(false);
      setError(null);
      processedInitialQuestionRef.current = ''; // 重置已处理的初始问题
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <>
      {/* 背景遮罩 - 全屏模式下隐藏 */}
      {!isFullscreen && <div className={styles.backdrop} onClick={onClose} />}
      
      {/* 问答区域 */}
      <div className={isFullscreen ? '' : styles.container}>
        <div className={`${styles.expandedArea} ${isFullscreen ? styles.fullscreen : ''}`}>
          {/* 头部 */}
          <div className={styles.header}>
            <h2 className={styles.title}>问答助理</h2>
            <div className={styles.headerActions}>
              <button 
                className={styles.actionButton}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFullscreen();
                }}
                title={isFullscreen ? "退出全屏" : "全屏"}
              >
                {isFullscreen ? <CompressOutlined /> : <ExpandOutlined />}
              </button>
              <button 
                className={styles.closeButton}
                onClick={(e) => {
                  e.stopPropagation();
                  onClose();
                }}
                title="关闭"
              >
                <CloseOutlined />
              </button>
            </div>
          </div>

          {/* 内容区域 */}
          <div className={styles.content}>
            {/* 错误提示 */}
            {error && (
              <div className={styles.errorMessage}>
                {error}
              </div>
            )}

            {/* 消息列表 */}
            <div className={styles.messagesContainer} ref={messagesContainerRef}>
              {!isInitialized ? (
                <div className={styles.loadingMessage}>
                  <LoadingOutlined />
                  正在初始化会话...
                </div>
              ) : messages.length === 0 ? (
                <div className={styles.emptyState}>
                  <div className={styles.emptyStateIcon}>
                    <RobotOutlined />
                  </div>
                  <div className={styles.emptyStateTitle}>问答助理</div>
                  <div className={styles.emptyStateDescription}>
                    我可以基于知识库收藏内容，为您搜索、总结、答疑解惑。
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`${styles.message} ${
                      msg.type === 'user' ? styles.userMessage : styles.assistantMessage
                    }`}
                  >
                    <div 
                      className={`${styles.messageContent} ${
                        msg.type === 'user' 
                          ? styles.userMessageContent 
                          : styles.assistantMessageContent
                      }`}
                    >
                      {msg.type === 'assistant' ? (
                        <>
                          <MarkdownRenderer 
                            content={msg.content} 
                            className={styles.markdownContent}
                          />
                          {/* 显示相关文档来源 */}
                          {msg.sources && msg.sources.length > 0 && (
                            <div className={styles.sourcesContainer}>
                              <div className={styles.sourcesTitle}>📚 相关文档：</div>
                              <div className={styles.sourcesList}>
                                {msg.sources.map((source, index) => (
                                  <a
                                    key={index}
                                    href={source.category_name 
                                      ? `/collection/${encodeURIComponent(source.category_name)}?highlight=${source.content_id}`
                                      : '#'}
                                    className={styles.sourceLink}
                                    onClick={(e) => {
                                      if (!source.category_name) {
                                        e.preventDefault();
                                        return;
                                      }
                                      // 关闭QA助理
                                      onClose();
                                    }}
                                  >
                                    {index + 1}. {source.title}
                                    {source.confidence_percentage && (
                                      <span className={styles.sourceConfidence}>
                                        ({Math.round(source.confidence_percentage)}%)
                                      </span>
                                    )}
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      ) : (
                        msg.content
                      )}
                    </div>
                    <div className={styles.messageTime}>
                      {msg.timestamp.toLocaleTimeString('zh-CN', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </div>
                  </div>
                ))
              )}

              {/* 正在思考指示器 */}
              {isLoading && (
                <div className={styles.message}>
                  <div className={styles.typingIndicator}>
                    正在思考中
                    <div className={styles.typingDots}>
                      <div className={styles.typingDot}></div>
                      <div className={styles.typingDot}></div>
                      <div className={styles.typingDot}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}