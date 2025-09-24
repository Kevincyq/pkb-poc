import api from './api';
import type { CategoryStatsResponse } from '../types/category';

export const getCategoryStats = async (): Promise<CategoryStatsResponse> => {
  try {
    console.log('Fetching category stats...');
    // 根据示例中的 API 路径修改
    const response = await api.get<CategoryStatsResponse>('/search/categories/stats');
    console.log('Category stats response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch category stats:', error);
    throw error;
  }
};