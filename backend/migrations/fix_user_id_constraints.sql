-- 修复 user_id 为 NULL 的问题
-- 执行前请备份数据库！

-- 1. 为所有 NULL 的 contents.user_id 设置默认用户
UPDATE contents 
SET user_id = (SELECT id FROM users WHERE email = 'test@pkb.local' LIMIT 1)
WHERE user_id IS NULL;

-- 2. 为所有 NULL 的 collections.user_id 设置默认用户
UPDATE collections 
SET user_id = (SELECT id FROM users WHERE email = 'test@pkb.local' LIMIT 1)
WHERE user_id IS NULL;

-- 3. 修改 Contents 表的约束
ALTER TABLE contents ALTER COLUMN user_id SET NOT NULL;

-- 4. 修改 Collections 表的约束
ALTER TABLE collections ALTER COLUMN user_id SET NOT NULL;

-- 5. 验证约束已添加
SELECT 
    table_name, 
    column_name, 
    is_nullable,
    data_type
FROM information_schema.columns 
WHERE table_name IN ('contents', 'collections') 
  AND column_name = 'user_id';

