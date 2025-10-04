import api from './api';

export interface UploadResponse {
  status: string;
  content_id: string;
  title: string;
  processing_status: string;
  chunks_created: number;
  file_size: number;
  message: string;
}

export interface ProcessingStatus {
  content_id: string;
  title: string;
  processing_status: 'uploaded' | 'parsing' | 'parsed' | 'processing' | 'completed' | 'error';
  parsing_status: 'pending' | 'parsing' | 'completed' | 'error';
  classification_status: 'pending' | 'quick_processing' | 'quick_done' | 'ai_processing' | 'completed' | 'error';
  show_classification: boolean;
  file_type: string;
  file_size: number;
  estimated_time: number;
  categories: Array<{
    id: string;
    name: string;
    confidence: number;
    reasoning?: string;
  }>;
  created_at: string | null;
}

export const uploadFile = async (
  file: File, 
  onProgress?: (progressEvent: { loaded: number; total: number; progress: number }) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/ingest/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress({
          loaded: progressEvent.loaded,
          total: progressEvent.total,
          progress: progress
        });
      }
    },
  });

  return response.data;
};

export interface BatchUploadResponse {
  status: string;
  total_files: number;
  success_count: number;
  error_count: number;
  results: Array<{
    index: number;
    filename: string;
    status: 'success' | 'error';
    result?: UploadResponse;
    error?: string;
  }>;
  message: string;
}

export const uploadMultipleFiles = async (files: File[]): Promise<BatchUploadResponse> => {
  const formData = new FormData();
  
  // 添加所有文件到FormData
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await api.post<BatchUploadResponse>('/ingest/upload-multiple', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const getProcessingStatus = async (contentId: string): Promise<ProcessingStatus> => {
  const response = await api.get<ProcessingStatus>(`/ingest/status/${contentId}`);
  return response.data;
};

export const validateFile = async (filename: string) => {
  const response = await api.get(`/document/validate/${filename}`);
  return response.data;
};
