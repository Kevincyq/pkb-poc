import api from './api';
import type { CategorySearchResponse } from '../types/collection';

export const getCategoryDocuments = async (
  categoryName: string,
  query?: string,
  limit: number = 20
): Promise<CategorySearchResponse> => {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  params.append('top_k', limit.toString());
  
  const url = `/search/category/${encodeURIComponent(categoryName)}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await api.get<CategorySearchResponse>(url);
  return response.data;
};