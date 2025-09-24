-- 清理数据库中包含NUL字符的数据
-- 这些数据可能导致"A string literal cannot contain NUL (0x00) characters"错误

-- 1. 查找包含NUL字符的内容
SELECT id, title, LENGTH(text) as text_length, 
       CASE WHEN text LIKE '%' || CHR(0) || '%' THEN 'Contains NUL' ELSE 'Clean' END as status
FROM contents 
WHERE text LIKE '%' || CHR(0) || '%';

-- 2. 查找包含NUL字符的chunks
SELECT id, content_id, LENGTH(text) as text_length,
       CASE WHEN text LIKE '%' || CHR(0) || '%' THEN 'Contains NUL' ELSE 'Clean' END as status
FROM chunks 
WHERE text LIKE '%' || CHR(0) || '%';

-- 3. 删除包含NUL字符的内容和相关数据
-- 注意：这会删除损坏的数据，请先备份！

-- 删除相关的分类关联
DELETE FROM content_categories 
WHERE content_id IN (
    SELECT id FROM contents WHERE text LIKE '%' || CHR(0) || '%'
);

-- 删除相关的chunks（会自动删除embeddings）
DELETE FROM chunks 
WHERE content_id IN (
    SELECT id FROM contents WHERE text LIKE '%' || CHR(0) || '%'
);

-- 删除损坏的内容记录
DELETE FROM contents WHERE text LIKE '%' || CHR(0) || '%';

-- 4. 清理包含NUL字符的chunks（如果有独立的）
DELETE FROM chunks WHERE text LIKE '%' || CHR(0) || '%';

-- 5. 验证清理结果
SELECT 'Contents with NUL characters' as table_name, COUNT(*) as count
FROM contents WHERE text LIKE '%' || CHR(0) || '%'
UNION ALL
SELECT 'Chunks with NUL characters' as table_name, COUNT(*) as count
FROM chunks WHERE text LIKE '%' || CHR(0) || '%';

COMMIT;
