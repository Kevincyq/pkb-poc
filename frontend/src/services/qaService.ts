/**
 * 问答服务 - 处理与后端问答API的交互
 */
import api from './api';
import type {
  QARequest,
  QAResponse,
  QAHistoryResponse,
  QAFeedbackRequest,
  QAServiceConfig,
  QAMessage
} from '../types/qa';

class QAService {
  private config: QAServiceConfig = {
    baseURL: '/qa',
    defaultModel: 'turing/gpt-4o-mini',
    defaultSearchType: 'hybrid',
    typewriterSpeed: 50,
    maxHistoryLength: 100
  };

  private currentSessionId: string | null = null;

  constructor() {
    this.initializeSession();
  }

  /**
   * 初始化会话 - 从localStorage恢复或创建新会话
   */
  private initializeSession(): void {
    const savedSessionId = localStorage.getItem('qa_session_id');
    if (savedSessionId) {
      this.currentSessionId = savedSessionId;
    } else {
      this.createNewSession();
    }
  }

  /**
   * 创建新会话
   */
  public createNewSession(): string {
    this.currentSessionId = this.generateSessionId();
    localStorage.setItem('qa_session_id', this.currentSessionId);
    return this.currentSessionId;
  }

  /**
   * 获取当前会话ID
   */
  public getCurrentSessionId(): string {
    if (!this.currentSessionId) {
      this.createNewSession();
    }
    return this.currentSessionId!;
  }

  /**
   * 生成会话ID
   */
  private generateSessionId(): string {
    return `qa_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 发送问题并获取回答
   */
  public async askQuestion(question: string, options?: Partial<QARequest>): Promise<QAResponse> {
    try {
      const request: QARequest = {
        question: question.trim(),
        session_id: this.getCurrentSessionId(),
        context_limit: 3000,
        model: this.config.defaultModel,
        search_type: this.config.defaultSearchType,
        ...options
      };

      console.log('🤖 Sending QA request:', request);
      console.log('🌐 Request URL:', `${this.config.baseURL}/ask`);
      console.log('📋 Full request config:', this.config);

      const response = await api.post<QAResponse>(`${this.config.baseURL}/ask`, request);
      
      console.log('✅ QA response received:', response.data);
      console.log('📊 Response status:', response.status);
      console.log('📋 Response headers:', response.headers);
      
      return response.data;
    } catch (error) {
      console.error('❌ QA request failed:', error);
      throw new Error(this.getErrorMessage(error));
    }
  }

  /**
   * 获取问答历史
   */
  public async getHistory(sessionId?: string, limit?: number): Promise<QAHistoryResponse> {
    try {
      const targetSessionId = sessionId || this.getCurrentSessionId();
      const params = {
        session_id: targetSessionId,
        limit: limit || this.config.maxHistoryLength
      };

      console.log('📚 Fetching QA history:', params);

      const response = await api.get<QAHistoryResponse>(`${this.config.baseURL}/history`, { params });
      
      console.log('✅ QA history received:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch QA history:', error);
      throw new Error(this.getErrorMessage(error));
    }
  }

  /**
   * 提交反馈
   */
  public async submitFeedback(qaId: string, feedback: 'good' | 'bad'): Promise<void> {
    try {
      const request: QAFeedbackRequest = { qa_id: qaId, feedback };
      
      console.log('👍 Submitting feedback:', request);
      
      await api.post(`${this.config.baseURL}/feedback`, request);
      
      console.log('✅ Feedback submitted successfully');
    } catch (error) {
      console.error('❌ Failed to submit feedback:', error);
      throw new Error(this.getErrorMessage(error));
    }
  }

  /**
   * 测试问答服务状态
   */
  public async testService(): Promise<any> {
    try {
      const response = await api.get(`${this.config.baseURL}/test`);
      return response.data;
    } catch (error) {
      console.error('❌ QA service test failed:', error);
      throw new Error(this.getErrorMessage(error));
    }
  }

  /**
   * 将历史记录转换为消息格式
   */
  public historyToMessages(history: QAHistoryResponse): QAMessage[] {
    const messages: QAMessage[] = [];
    
    // 按时间顺序排序（最早的在前）
    const sortedHistory = [...history.history].reverse();
    
    sortedHistory.forEach((item) => {
      // 用户问题
      messages.push({
        id: `user_${item.id}`,
        type: 'user',
        content: item.question,
        timestamp: new Date(item.created_at)
      });
      
      // AI回答
      messages.push({
        id: `assistant_${item.id}`,
        type: 'assistant',
        content: item.answer,
        timestamp: new Date(item.created_at)
      });
    });
    
    return messages;
  }

  /**
   * 获取配置
   */
  public getConfig(): QAServiceConfig {
    return { ...this.config };
  }

  /**
   * 更新配置
   */
  public updateConfig(newConfig: Partial<QAServiceConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * 清除当前会话
   */
  public clearSession(): void {
    localStorage.removeItem('qa_session_id');
    this.currentSessionId = null;
  }

  /**
   * 提取错误信息
   */
  private getErrorMessage(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.response?.data?.error) {
      return error.response.data.error;
    }
    if (error.response?.status) {
      return `请求失败 (${error.response.status}): ${error.response.statusText || '未知错误'}`;
    }
    if (error.message) {
      return error.message;
    }
    return '问答服务暂时不可用，请稍后重试';
  }
}

// 导出单例实例
export const qaService = new QAService();
export default qaService;
