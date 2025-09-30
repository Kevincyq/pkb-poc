import React, { useState, useRef } from 'react';
import { Input } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import styles from './AIInput.module.css';
import QAAssistant from '../QA/QAAssistant';
import { useQAAssistant } from '../../hooks/useQAAssistant';

interface AIInputProps {
  onSend?: (value: string) => void; // 保持向后兼容，但现在主要用问答助理
}

export default function AIInput({ onSend: _ }: AIInputProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<any>(null);
  const qaAssistant = useQAAssistant();

  // 处理输入框点击 - 打开问答助理
  const handleInputClick = () => {
    qaAssistant.show(inputValue.trim());
  };

  // 处理输入框聚焦 - 打开问答助理
  const handleInputFocus = () => {
    qaAssistant.show(inputValue.trim());
  };

  // 处理发送按钮点击
  const handleSend = () => {
    const value = inputValue.trim();
    if (value) {
      qaAssistant.show(value);
      setInputValue(''); // 清空输入框
    }
  };

  // 处理回车键
  const handlePressEnter = (e: React.KeyboardEvent<HTMLInputElement>) => {
    e.preventDefault(); // 阻止默认行为
    const value = (e.target as HTMLInputElement).value.trim();
    if (value) {
      qaAssistant.show(value);
      setInputValue(''); // 清空输入框
    }
  };

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  return (
    <>
      <div className={styles.wrapper}>
        <Input
          ref={inputRef}
          className={styles.input}
          value={inputValue}
          onChange={handleInputChange}
          onClick={handleInputClick}
          onFocus={handleInputFocus}
          placeholder="我可以基于知识库收藏内容，为您搜索、总结、答疑解惑。"
          suffix={
            <SendOutlined 
              className={styles.sendIcon} 
              onClick={handleSend}
              style={{ cursor: 'pointer' }}
            />
          }
          onPressEnter={handlePressEnter}
        />
      </div>

      {/* 问答助理浮层 */}
      <QAAssistant
        visible={qaAssistant.visible}
        onClose={qaAssistant.hide}
        initialQuestion={qaAssistant.initialQuestion}
      />
    </>
  );
}