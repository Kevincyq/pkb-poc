import React, { useState, useRef } from 'react';
import { Input, Dropdown, Checkbox } from 'antd';
const { TextArea } = Input;
import { SendOutlined, DownOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import styles from './AIInput.module.css';
import QAAssistant from '../QA/QAAssistant';
import { useQAAssistant } from '../../hooks/useQAAssistant';

interface AIInputProps {
  onSend?: (value: string) => void; // 保持向后兼容，但现在主要用问答助理
}

// 系统分类列表
const SYSTEM_CATEGORIES = [
  { key: 'all', label: 'All' },
  { key: 'Business', label: 'Business' },
  { key: 'Technology', label: 'Technology' },
  { key: 'Learning', label: 'Learning' },
  { key: 'Life', label: 'Life' },
  { key: 'Art', label: 'Art' },
];

export default function AIInput({ onSend: _ }: AIInputProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<any>(null);
  const qaAssistant = useQAAssistant();
  const [selectedCategories, setSelectedCategories] = useState<string[]>(['all']); // 默认选择All
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // 处理分类选择变化
  const handleCategoryChange = (categoryKey: string, checked: boolean) => {
    if (categoryKey === 'all') {
      // 如果选择All，清空其他选择
      setSelectedCategories(checked ? ['all'] : []);
    } else {
      // 如果选择其他分类，移除All
      const newCategories = checked
        ? [...selectedCategories.filter(c => c !== 'all'), categoryKey]
        : selectedCategories.filter(c => c !== categoryKey);
      setSelectedCategories(newCategories.length > 0 ? newCategories : ['all']);
    }
  };

  // 处理发送按钮点击
  const handleSend = () => {
    const value = inputValue.trim();
    if (value) {
      // 传递选中的分类信息（排除'all'，因为'all'表示全部）
      const categories = selectedCategories.filter(c => c !== 'all');
      qaAssistant.show(value, categories.length > 0 ? categories : undefined);
      setInputValue(''); // 清空输入框
    }
  };

  // 处理回车键（Ctrl+Enter 或 Cmd+Enter 发送，单独 Enter 换行）
  const handlePressEnter = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault(); // 阻止默认行为
      const value = inputValue.trim();
      if (value) {
        // 传递选中的分类信息
        const categories = selectedCategories.filter(c => c !== 'all');
        qaAssistant.show(value, categories.length > 0 ? categories : undefined);
        setInputValue(''); // 清空输入框
      }
    }
    // 单独 Enter 键允许换行，不做处理
  };

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  // 构建分类下拉菜单
  const categoryMenu: MenuProps = {
    items: SYSTEM_CATEGORIES.map(category => ({
      key: category.key,
      label: (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Checkbox
            checked={selectedCategories.includes(category.key)}
            onChange={(e) => handleCategoryChange(category.key, e.target.checked)}
            onClick={(e) => e.stopPropagation()}
          />
          <span>{category.label}</span>
        </div>
      ),
    })),
  };

  // 获取胶囊按钮显示文本
  const getCapsuleText = () => {
    if (selectedCategories.length === 0 || (selectedCategories.length === 1 && selectedCategories[0] === 'all')) {
      return 'All inspirations';
    }
    if (selectedCategories.length === 1) {
      return SYSTEM_CATEGORIES.find(c => c.key === selectedCategories[0])?.label || 'All inspirations';
    }
    return `${selectedCategories.length} selected`;
  };

  return (
    <>
      <div className={styles.wrapper}>
        <div className={styles.inputContainer}>
          {/* 分类选择胶囊按钮 */}
          <Dropdown 
            menu={categoryMenu} 
            trigger={['click']}
            placement="topLeft"
            overlayClassName={styles.categoryDropdown}
            open={dropdownOpen}
            onOpenChange={(open) => {
              console.log('Dropdown onOpenChange:', open);
              setDropdownOpen(open);
            }}
            getPopupContainer={() => document.body}
          >
            <div 
              className={styles.categoryCapsule}
              onClick={(e) => {
                console.log('Capsule clicked');
                e.preventDefault();
                e.stopPropagation();
                setDropdownOpen(!dropdownOpen);
              }}
            >
              <span className={styles.capsuleText}>{getCapsuleText()}</span>
              <DownOutlined className={styles.capsuleIcon} style={{ 
                transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s'
              }} />
            </div>
          </Dropdown>
          
          <div className={styles.textAreaWrapper}>
            <TextArea
              ref={inputRef}
              className={styles.input}
              value={inputValue}
              onChange={handleInputChange}
              placeholder="Ask a question based on the knowledge base"
              onPressEnter={handlePressEnter}
              autoSize={{ minRows: 3, maxRows: 6 }}
              rows={3}
            />
            <SendOutlined 
              className={styles.sendIcon} 
              onClick={handleSend}
              style={{ cursor: 'pointer' }}
            />
          </div>
        </div>
      </div>

      {/* 问答助理浮层 */}
      <QAAssistant
        visible={qaAssistant.visible}
        onClose={qaAssistant.hide}
        initialQuestion={qaAssistant.initialQuestion}
        selectedCategories={qaAssistant.selectedCategories}
      />
    </>
  );
}