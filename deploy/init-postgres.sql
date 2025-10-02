-- PKB PostgreSQL 初始化脚本
-- 自动安装必要的扩展

-- 安装 pgvector 扩展（用于向量搜索）
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展安装
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- 输出确认信息
\echo 'PKB PostgreSQL 初始化完成：pgvector 扩展已安装'
