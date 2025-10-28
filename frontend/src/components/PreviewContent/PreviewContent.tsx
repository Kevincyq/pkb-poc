import React, { useState, useEffect } from 'react';
import { Tag, Spin } from 'antd';
import { formatDateTime } from '../../utils/dateUtils';
import styles from './PreviewContent.module.css';

interface Document {
  id: string;
  title: string;
  modality: string;
  source_uri: string;
  created_at: string;
  category_name?: string;
  tags?: Array<{ name: string }>;
}

interface PreviewContentProps {
  document: Document;
}

export default function PreviewContent({ document }: PreviewContentProps) {
  const [imageLoading, setImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  const [imageSrc, setImageSrc] = useState<string>('');

  // 获取API基础URL
  const getApiBaseUrl = () => {
    return import.meta.env.VITE_API_BASE_URL || 
      (window.location.hostname === 'localhost' 
        ? 'http://localhost:8003/api' 
        : 'https://pkb-test.kmchat.cloud/api'
      );
  };

  // 获取图片URL（优先使用缩略图，失败时使用原图）
  const getImageUrls = (sourceUri: string) => {
    const apiBaseUrl = getApiBaseUrl();
    
    let fileName = '';
    
    // 提取文件名或文件ID
    if (sourceUri.includes('webui://')) {
      fileName = sourceUri.replace('webui://', '');
    } else if (sourceUri.includes('nextcloud://')) {
      fileName = sourceUri.replace('nextcloud://', '');
    } else if (sourceUri.includes('google_drive://')) {
      fileName = sourceUri.replace('google_drive://', '');
    } else {
      fileName = sourceUri;
    }
    
    return {
      // 优先使用缩略图（更快加载）
      thumbnail: `${apiBaseUrl}/files/thumbnail/${encodeURIComponent(fileName)}`,
      // 备用原图（高质量）
      original: `${apiBaseUrl}/files/${encodeURIComponent(fileName)}`
    };
  };

  useEffect(() => {
    if (document.modality === 'image') {
      console.log('🖼️ Starting image preview for:', document.title);
      setImageLoading(true);
      setImageError(false);
      
      const urls = getImageUrls(document.source_uri);
      
      // 先尝试加载缩略图
      const img = new Image();
      img.onload = () => {
        console.log('✅ Thumbnail loaded successfully for preview');
        setImageSrc(urls.thumbnail);
        setImageLoading(false);
        
        // 后台预加载原图，用于更高质量显示
        const originalImg = new Image();
        originalImg.onload = () => {
          console.log('✅ Original image preloaded, switching to high quality');
          setImageSrc(urls.original);
        };
        originalImg.onerror = () => {
          console.log('⚠️ Original image failed to load, keeping thumbnail');
        };
        originalImg.src = urls.original;
      };
      
      img.onerror = () => {
        console.log('❌ Thumbnail failed, trying original image');
        // 缩略图失败，直接尝试原图
        const originalImg = new Image();
        originalImg.onload = () => {
          console.log('✅ Original image loaded successfully');
          setImageSrc(urls.original);
          setImageLoading(false);
        };
        originalImg.onerror = () => {
          console.log('❌ Both thumbnail and original failed');
          setImageError(true);
          setImageLoading(false);
        };
        originalImg.src = urls.original;
      };
      
      img.src = urls.thumbnail;
    }
  }, [document]);

  if (document.modality === 'image') {
    return (
      <div className={styles.previewContainer}>
        {/* 图片预览区域 */}
        <div className={styles.imageContainer}>
          {imageLoading && (
            <div className={styles.loadingContainer}>
              <Spin size="large" />
              <p style={{ marginTop: '16px', color: '#666' }}>正在加载图片...</p>
            </div>
          )}
          
          {!imageLoading && !imageError && (
            <img
              src={imageSrc}
              alt={document.title}
              className={styles.previewImage}
              style={{ display: imageLoading ? 'none' : 'block' }}
            />
          )}
          
          {!imageLoading && imageError && (
            <div className={styles.errorContainer}>
              <div className={styles.errorIcon}>🖼️</div>
              <p>图片加载失败</p>
              <p style={{ fontSize: '12px', color: '#999' }}>
                {document.title}
              </p>
            </div>
          )}
        </div>
        
        {/* 文件信息 */}
        <div className={styles.infoContainer}>
          <p><strong>文件名：</strong>{document.title}</p>
          <p><strong>来源：</strong>{document.source_uri.includes('webui://') ? 'WebUI上传' : '其他'}</p>
          <p><strong>创建时间：</strong>{formatDateTime(document.created_at)}</p>
          {document.category_name && (
            <p><strong>分类：</strong>{document.category_name}</p>
          )}
          {document.tags && document.tags.length > 0 && (
            <p>
              <strong>标签：</strong>
              {document.tags.map((tag: any, index: number) => (
                <Tag key={index} color="blue" style={{ marginRight: '4px', marginTop: '4px' }}>
                  {tag.name}
                </Tag>
              ))}
            </p>
          )}
        </div>
      </div>
    );
  }

  // 非图片文件的预览
  return (
    <div className={styles.previewContainer}>
      <div className={styles.nonImageContainer}>
        <div className={styles.fileIcon}>📄</div>
        <h3>{document.title}</h3>
        <p>此文件类型暂不支持预览</p>
      </div>
      
      <div className={styles.infoContainer}>
        <p><strong>文件名：</strong>{document.title}</p>
        <p><strong>来源：</strong>{document.source_uri.includes('webui://') ? 'WebUI上传' : '其他'}</p>
        <p><strong>创建时间：</strong>{formatDateTime(document.created_at)}</p>
        {document.category_name && (
          <p><strong>分类：</strong>{document.category_name}</p>
        )}
        {document.tags && document.tags.length > 0 && (
          <p>
            <strong>标签：</strong>
            {document.tags.map((tag: any, index: number) => (
              <Tag key={index} color="blue" style={{ marginRight: '4px', marginTop: '4px' }}>
                {tag.name}
              </Tag>
            ))}
          </p>
        )}
      </div>
    </div>
  );
}
