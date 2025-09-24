-- 0. 检查contents表的结构
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'contents';

-- 1. 检查所有图片文件的基本信息和处理状态
SELECT 
    id,
    title,
    source_uri,
    modality,
    meta->>'processing_status' as processing_status,
    meta->>'error' as error_message,
    created_at,
    updated_at
FROM contents 
WHERE modality = 'image'
ORDER BY created_at DESC;

-- 2. 检查图片文件的分类结果
SELECT 
    c.id,
    c.title,
    c.source_uri,
    c.meta->>'processing_status' as processing_status,
    cat.name as category_name,
    cc.confidence as category_confidence,
    c.created_at,
    c.updated_at
FROM contents c
LEFT JOIN content_categories cc ON c.id = cc.content_id
LEFT JOIN categories cat ON cc.category_id = cat.id
WHERE c.modality = 'image'
ORDER BY c.created_at DESC;

-- 3. 检查图片文件的文本提取结果
SELECT 
    c.id as content_id,
    c.title,
    c.source_uri,
    c.meta->>'processing_status' as processing_status,
    ch.id as chunk_id,
    LEFT(ch.text, 100) as extracted_text_preview,
    ch.chunk_type,
    c.created_at,
    c.updated_at
FROM contents c
LEFT JOIN chunks ch ON c.id = ch.content_id
WHERE c.modality = 'image'
ORDER BY c.created_at DESC;

-- 4. 检查处理失败的图片
SELECT 
    id,
    title,
    source_uri,
    meta->>'processing_status' as processing_status,
    meta->>'error' as error_message,
    created_at,
    updated_at
FROM contents 
WHERE modality = 'image' 
AND (
    meta->>'processing_status' = 'failed' 
    OR meta->>'error' IS NOT NULL
)
ORDER BY created_at DESC;

-- 5. 统计图片处理状态
SELECT 
    modality,
    COUNT(*) as total_files,
    COUNT(*) FILTER (WHERE meta->>'processing_status' = 'completed') as completed,
    COUNT(*) FILTER (WHERE meta->>'processing_status' = 'pending') as pending,
    COUNT(*) FILTER (WHERE meta->>'processing_status' = 'failed') as failed,
    COUNT(DISTINCT id) FILTER (WHERE EXISTS (
        SELECT 1 FROM chunks WHERE content_id = contents.id
    )) as with_chunks,
    COUNT(DISTINCT id) FILTER (WHERE EXISTS (
        SELECT 1 FROM content_categories WHERE content_id = contents.id
    )) as with_categories,
    MIN(created_at) as earliest_file,
    MAX(created_at) as latest_file
FROM contents 
WHERE modality = 'image'
GROUP BY modality;

-- 6. 检查最近处理的图片文件
SELECT 
    c.id,
    c.title,
    c.source_uri,
    c.modality,
    c.meta->>'processing_status' as processing_status,
    c.created_at,
    c.updated_at,
    CASE 
        WHEN ch.id IS NULL THEN '未提取文本'
        ELSE '已提取文本'
    END as text_status,
    CASE 
        WHEN cc.category_id IS NULL THEN '未分类'
        ELSE '已分类'
    END as category_status,
    cat.name as category_name,
    cc.confidence as category_confidence
FROM contents c
LEFT JOIN chunks ch ON c.id = ch.content_id
LEFT JOIN content_categories cc ON c.id = cc.content_id
LEFT JOIN categories cat ON cc.category_id = cat.id
WHERE c.modality = 'image'
ORDER BY c.created_at DESC
LIMIT 10;