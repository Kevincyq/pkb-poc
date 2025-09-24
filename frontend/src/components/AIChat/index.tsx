import { useState } from 'react';
import { Input, Button } from 'antd';
import styles from './index.module.css';

interface AIChatProps {
  onClose?: () => void;
  onFullscreen?: () => void;
}

export default function AIChat({ onClose, onFullscreen }: AIChatProps) {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState<{
    type: 'question' | 'answer';
    content: string;
  }[]>([]);

  const handleSend = async () => {
    if (!message.trim()) return;
    
    // 添加用户问题到对话
    setConversation(prev => [...prev, { type: 'question', content: message }]);
    setLoading(true);

    try {
      // TODO: 调用后端API获取回答
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 添加AI回答到对话
      setConversation(prev => [...prev, {
        type: 'answer',
        content: '根据个人知识库内容：\n1. 示例回答内容一\n2. 示例回答内容二\n3. 示例回答内容三'
      }]);
    } catch (error) {
      setConversation(prev => [...prev, {
        type: 'answer',
        content: '抱歉，未能成功完成查询。请稍后再试。'
      }]);
    } finally {
      setLoading(false);
      setMessage('');
    }
  };

  return (
    <div className={styles.container}>
      {/* 对话框头部 */}
      <div className={styles.header}>
        <span>问知识助理</span>
        <div className={styles.actions}>
          <Button type="text" onClick={onFullscreen}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
            </svg>
          </Button>
          <Button type="text" onClick={onClose}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </Button>
        </div>
      </div>

      {/* 对话内容区域 */}
      <div className={styles.messages}>
        {conversation.map((msg, index) => (
          <div key={index} className={msg.type === 'question' ? styles.question : styles.answer}>
            {msg.type === 'answer' && loading && index === conversation.length - 1 ? (
              <div className={styles.loading}>
                <p>正在查询中...</p>
                <p className={styles.hint}>请稍等片刻完成查询</p>
              </div>
            ) : (
              <div className={styles.messageContent}>
                {msg.content.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
                {msg.type === 'answer' && (
                  <div className={styles.messageActions}>
                    <Button type="text" size="small">复制</Button>
                    <Button type="text" size="small">引用</Button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 输入框区域 */}
      <div className={styles.inputArea}>
        <Input
          value={message}
          onChange={e => setMessage(e.target.value)}
          onPressEnter={handleSend}
          placeholder="我可以基于知识库收藏内容，为您搜索、总结、答疑解惑。"
          disabled={loading}
          suffix={
            <Button 
              type="text"
              onClick={handleSend}
              disabled={loading}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </Button>
          }
        />
      </div>
    </div>
  );
}
