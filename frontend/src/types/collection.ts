export interface CategoryDetail {
  id: string;
  name: string;
  description?: string;
  color: string;
}

export interface CollectionDocument {
  content_id: string;
  chunk_id: string;
  title: string;
  modality: 'text' | 'image' | 'pdf';
  source_uri: string;
  created_at: string;
  category?: string;
  category_name?: string;
  category_color?: string;
  category_confidence?: number;
  score?: number;
  text?: string;
  tags?: string;
  match_type?: string;
  chunk_type?: string;
  thumbnailUrl?: string;
}

export interface CategorySearchResponse {
  category: CategoryDetail;
  results: CollectionDocument[];
  total: number;
}
