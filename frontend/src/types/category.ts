export interface Category {
  id: string;
  name: string;
  color: string;
  content_count: number;
}

export interface CategoryStatsResponse {
  categories: Category[];
}
