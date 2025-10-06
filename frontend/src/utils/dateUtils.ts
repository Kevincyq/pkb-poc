/**
 * 日期时间处理工具函数
 * 统一处理服务器返回的UTC时间到本地时区的转换
 */

/**
 * 格式化日期时间 - 显示本地时区的完整日期时间
 * @param dateString - 服务器返回的日期字符串（UTC时间）
 * @returns 格式化的本地时间字符串，如 "2025/10/6 12:35:21"
 */
export const formatDateTime = (dateString: string): string => {
  if (!dateString) return '';
  
  try {
    // 标准化UTC时间字符串
    const normalizedDateString = normalizeUTCDateString(dateString);
    
    // 创建Date对象，JavaScript会自动处理UTC到本地时区的转换
    const date = new Date(normalizedDateString);
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString, 'normalized:', normalizedDateString);
      return dateString;
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    console.error('Error formatting date:', error, 'dateString:', dateString);
    return dateString;
  }
};

/**
 * 格式化日期 - 只显示日期部分
 * @param dateString - 服务器返回的日期字符串（UTC时间）
 * @returns 格式化的本地日期字符串，如 "2025/10/6"
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  
  try {
    // 标准化UTC时间字符串
    const normalizedDateString = normalizeUTCDateString(dateString);
    const date = new Date(normalizedDateString);
    
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString, 'normalized:', normalizedDateString);
      return dateString;
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}/${month}/${day}`;
  } catch (error) {
    console.error('Error formatting date:', error, 'dateString:', dateString);
    return dateString;
  }
};

/**
 * 格式化相对时间 - 显示相对于现在的时间
 * @param dateString - 服务器返回的日期字符串（UTC时间）
 * @returns 相对时间字符串，如 "2小时前", "昨天", "3天前"
 */
export const formatRelativeTime = (dateString: string): string => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 1) {
      return '刚刚';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours}小时前`;
    } else if (diffDays === 1) {
      return '昨天';
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return formatDate(dateString);
    }
  } catch (error) {
    console.error('Error formatting relative time:', error, 'dateString:', dateString);
    return formatDate(dateString);
  }
};

/**
 * 检查日期字符串是否包含时区信息
 * @param dateString - 日期字符串
 * @returns 是否包含时区信息
 */
export const hasTimezoneInfo = (dateString: string): boolean => {
  // 检查是否包含时区标识符，如 'Z', '+08:00', '-05:00' 等
  return /[+-]\d{2}:\d{2}|Z$/i.test(dateString);
};

/**
 * 确保日期字符串被正确解析为UTC时间
 * @param dateString - 服务器返回的日期字符串
 * @returns 标准化的日期字符串
 */
export const normalizeUTCDateString = (dateString: string): string => {
  if (!dateString) return dateString;
  
  // 如果已经包含时区信息，直接返回
  if (hasTimezoneInfo(dateString)) {
    return dateString;
  }
  
  // 如果没有时区信息，假设是UTC时间，添加'Z'后缀
  if (dateString.includes('T') && !dateString.endsWith('Z')) {
    return dateString + 'Z';
  }
  
  return dateString;
};
