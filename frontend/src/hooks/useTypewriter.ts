/**
 * 打字机效果Hook - 实现逐字符显示文本的动画效果
 */
import { useState, useEffect, useRef, useCallback } from 'react';

export interface TypewriterOptions {
  speed?: number; // 每个字符的延迟时间（毫秒）
  startDelay?: number; // 开始前的延迟时间（毫秒）
  onComplete?: () => void; // 完成回调
  onCharacter?: (char: string, index: number) => void; // 每个字符的回调
}

export interface TypewriterResult {
  displayText: string;
  isTyping: boolean;
  isComplete: boolean;
  start: () => void;
  stop: () => void;
  reset: () => void;
  skip: () => void; // 跳过动画，直接显示完整文本
}

/**
 * 打字机效果Hook
 * @param text 要显示的完整文本
 * @param options 配置选项
 * @returns 打字机控制对象
 */
export function useTypewriter(
  text: string,
  options: TypewriterOptions = {}
): TypewriterResult {
  const {
    speed = 50,
    startDelay = 0,
    onComplete,
    onCharacter
  } = options;

  const [displayText, setDisplayText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  
  const timeoutRef = useRef<number | null>(null);
  const currentIndexRef = useRef(0);
  const isStoppedRef = useRef(false);

  // 清理定时器
  const clearTimer = useCallback(() => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // 打字机核心逻辑
  const typeNextCharacter = useCallback(() => {
    if (isStoppedRef.current || currentIndexRef.current >= text.length) {
      setIsTyping(false);
      setIsComplete(true);
      onComplete?.();
      return;
    }

    const currentChar = text[currentIndexRef.current];
    const newDisplayText = text.slice(0, currentIndexRef.current + 1);
    
    setDisplayText(newDisplayText);
    onCharacter?.(currentChar, currentIndexRef.current);
    
    currentIndexRef.current += 1;

    // 根据字符类型调整速度
    let nextDelay = speed;
    if (currentChar === '。' || currentChar === '！' || currentChar === '？') {
      nextDelay = speed * 3; // 句号等标点符号后停顿更久
    } else if (currentChar === '，' || currentChar === '；') {
      nextDelay = speed * 2; // 逗号等停顿稍久
    } else if (currentChar === '\n') {
      nextDelay = speed * 2; // 换行后停顿
    }

    timeoutRef.current = window.setTimeout(typeNextCharacter, nextDelay);
  }, [text, speed, onComplete, onCharacter]);

  // 开始打字机效果
  const start = useCallback(() => {
    if (isTyping || isComplete) return;
    
    isStoppedRef.current = false;
    setIsTyping(true);
    setIsComplete(false);
    currentIndexRef.current = 0;
    setDisplayText('');

    if (startDelay > 0) {
      timeoutRef.current = window.setTimeout(typeNextCharacter, startDelay);
    } else {
      typeNextCharacter();
    }
  }, [isTyping, isComplete, startDelay, typeNextCharacter]);

  // 停止打字机效果
  const stop = useCallback(() => {
    isStoppedRef.current = true;
    setIsTyping(false);
    clearTimer();
  }, [clearTimer]);

  // 重置打字机效果
  const reset = useCallback(() => {
    stop();
    setDisplayText('');
    setIsComplete(false);
    currentIndexRef.current = 0;
  }, [stop]);

  // 跳过动画，直接显示完整文本
  const skip = useCallback(() => {
    stop();
    setDisplayText(text);
    setIsComplete(true);
    currentIndexRef.current = text.length;
    onComplete?.();
  }, [stop, text, onComplete]);

  // 当文本改变时重置状态
  useEffect(() => {
    reset();
  }, [text, reset]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

  return {
    displayText,
    isTyping,
    isComplete,
    start,
    stop,
    reset,
    skip
  };
}

/**
 * 批量打字机效果Hook - 用于处理多条消息的连续打字机效果
 */
export function useBatchTypewriter(
  texts: string[],
  options: TypewriterOptions = {}
): {
  currentIndex: number;
  displayTexts: string[];
  isTyping: boolean;
  allComplete: boolean;
  startAll: () => void;
  stopAll: () => void;
  resetAll: () => void;
  skipAll: () => void;
} {
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [displayTexts, setDisplayTexts] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [allComplete, setAllComplete] = useState(false);

  const currentTypewriter = useTypewriter(
    currentIndex >= 0 && currentIndex < texts.length ? texts[currentIndex] : '',
    {
      ...options,
      onComplete: () => {
        // 当前文本完成，移动到下一个
        setDisplayTexts(prev => {
          const newTexts = [...prev];
          if (currentIndex >= 0 && currentIndex < texts.length) {
            newTexts[currentIndex] = texts[currentIndex];
          }
          return newTexts;
        });

        if (currentIndex < texts.length - 1) {
          setCurrentIndex(prev => prev + 1);
        } else {
          setIsTyping(false);
          setAllComplete(true);
          options.onComplete?.();
        }
      }
    }
  );

  // 开始所有文本的打字机效果
  const startAll = useCallback(() => {
    if (texts.length === 0) return;
    
    setDisplayTexts(new Array(texts.length).fill(''));
    setCurrentIndex(0);
    setIsTyping(true);
    setAllComplete(false);
  }, [texts.length]);

  // 停止所有打字机效果
  const stopAll = useCallback(() => {
    currentTypewriter.stop();
    setIsTyping(false);
  }, [currentTypewriter]);

  // 重置所有打字机效果
  const resetAll = useCallback(() => {
    currentTypewriter.reset();
    setCurrentIndex(-1);
    setDisplayTexts([]);
    setIsTyping(false);
    setAllComplete(false);
  }, [currentTypewriter]);

  // 跳过所有动画
  const skipAll = useCallback(() => {
    stopAll();
    setDisplayTexts([...texts]);
    setCurrentIndex(texts.length - 1);
    setAllComplete(true);
    options.onComplete?.();
  }, [stopAll, texts, options]);

  // 当当前索引改变时，启动对应的打字机效果
  useEffect(() => {
    if (currentIndex >= 0 && currentIndex < texts.length) {
      currentTypewriter.start();
    }
  }, [currentIndex, texts.length, currentTypewriter]);

  // 更新当前显示的文本
  useEffect(() => {
    if (currentIndex >= 0) {
      setDisplayTexts(prev => {
        const newTexts = [...prev];
        newTexts[currentIndex] = currentTypewriter.displayText;
        return newTexts;
      });
    }
  }, [currentIndex, currentTypewriter.displayText]);

  return {
    currentIndex,
    displayTexts,
    isTyping,
    allComplete,
    startAll,
    stopAll,
    resetAll,
    skipAll
  };
}
