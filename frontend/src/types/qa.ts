/**
 * 问答系统相关的类型定义
 */

export interface QAMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isTyping?: boolean; // 用于打字机效果
}

export interface QASession {
  id: string;
  messages: QAMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface QARequest {
  question: string;
  session_id?: string;
  context_limit?: number;
  model?: string;
  search_type?: 'keyword' | 'semantic' | 'hybrid';
  category_filter?: string;
}

export interface QAResponse {
  question: string;
  answer: string;
  session_id: string;
  confidence: number;
  sources: Array<{
    title: string;
    text: string;
    source_uri: string;
    score: number;
    content_id: string;
    category_name?: string;
    modality: string;
    confidence_percentage: number;
  }>;
  formatted_sources?: string; // 新增：格式化的来源信息
  qa_id: string;
  tokens_used?: number;
  response_time?: number;
}

export interface QAHistoryItem {
  id: string;
  question: string;
  answer: string;
  session_id: string;
  confidence: number;
  created_at: string;
  feedback?: 'good' | 'bad';
}

export interface QAHistoryResponse {
  session_id: string;
  history: QAHistoryItem[];
  total: number;
}

export interface QAFeedbackRequest {
  qa_id: string;
  feedback: 'good' | 'bad';
}

export interface QAServiceConfig {
  baseURL: string;
  defaultModel: string;
  defaultSearchType: 'keyword' | 'semantic' | 'hybrid';
  typewriterSpeed: number; // 打字机效果速度（毫秒）
  maxHistoryLength: number;
}
