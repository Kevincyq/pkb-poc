"""
增强搜索服务
支持关键词搜索、语义搜索和混合搜索
"""
import re
import time
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.sql import text
from app.models import Content, Chunk, QAHistory, Category, ContentCategory, Collection
from app.services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    def search(
        self, 
        query: str, 
        top_k: int = 10, 
        search_type: str = "hybrid",
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        统一搜索接口
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            search_type: 搜索类型 ("keyword", "semantic", "hybrid")
            filters: 过滤条件 {"modality": "text", "created_by": "memo.api"}
        
        Returns:
            搜索结果字典
        """
        start_time = time.time()
        
        try:
            if search_type == "keyword":
                results = self._keyword_search(query, top_k, filters)
            elif search_type == "semantic":
                results = self._semantic_search(query, top_k, filters)
            else:  # hybrid
                results = self._hybrid_search(query, top_k, filters)
            
            response_time = time.time() - start_time
            
            # 更新搜索统计
            self._update_search_stats(query, len(results))
            
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "response_time": response_time,
                "search_type": search_type,
                "embedding_enabled": self.embedding_service.is_enabled()
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            error_response = {
                "query": query,
                "results": [],
                "total": 0,
                "response_time": time.time() - start_time,
                "search_type": search_type,
                "embedding_enabled": self.embedding_service.is_enabled(),
                "error": str(e)
            }
            logger.error(f"Search error response: {error_response}")
            return error_response
    
    def _keyword_search(self, query: str, top_k: int, filters: Optional[Dict] = None) -> List[Dict]:
        """关键词搜索"""
        try:
            # 构建基础查询，包含分类信息
            base_query = self.db.query(
                Chunk, Content, Category.name.label('category_name'), 
                Category.color.label('category_color'),
                ContentCategory.confidence.label('category_confidence')
            ).select_from(Chunk).join(
                Content, Chunk.content_id == Content.id
            ).outerjoin(
                ContentCategory, Content.id == ContentCategory.content_id
            ).outerjoin(
                Category, ContentCategory.category_id == Category.id
            )
            
            # 应用过滤条件
            if filters:
                base_query = self._apply_filters(base_query, filters)
            
            # 对查询进行预处理
            query = query.strip()
            if not query:
                return []
            
            # 改进中文搜索支持
            search_terms = self._extract_search_terms(query)
            
            # 1. 精确匹配（包含元数据关键词）
            conditions = []
            params = {}
            
            # 在文本和标题中搜索
            conditions.append(text("chunks.text LIKE :query"))
            conditions.append(text("contents.title LIKE :query"))
            params['query'] = f"%{query}%"
            
            # 在元数据关键词中搜索
            for term in search_terms:
                if term != query:  # 避免重复
                    param_name = f"term_{len(params)}"
                    conditions.extend([
                        text(f"chunks.text LIKE :{param_name}"),
                        text(f"contents.title LIKE :{param_name}"),
                        text(f"contents.meta->>'keywords' LIKE :{param_name}")
                    ])
                    params[param_name] = f"%{term}%"
            
            results = base_query.filter(or_(*conditions)).params(**params).limit(top_k).all()
            
            # 2. 如果没有结果，尝试分词匹配
            if not results:
                # 将查询分词
                words = [w.strip() for w in query.split() if w.strip()]
                if words:
                    conditions = []
                    params = {}
                    for i, word in enumerate(words):
                        param_name = f"word_{i}"
                        conditions.append(
                            or_(
                                text(f"chunks.text LIKE :{param_name}"),
                                text(f"contents.title LIKE :{param_name}")
                            )
                        )
                        params[param_name] = f"%{word}%"
                    results = base_query.filter(and_(*conditions)).params(**params).limit(top_k).all()
            
            # 3. 如果还是没有结果，尝试更宽松的匹配
            if not results:
                # 使用任意一个词匹配
                words = [w.strip() for w in query.split() if w.strip()]
                if words:
                    conditions = []
                    params = {}
                    for i, word in enumerate(words):
                        param_name = f"word_{i}"
                        conditions.append(
                            or_(
                                text(f"chunks.text LIKE :{param_name}"),
                                text(f"contents.title LIKE :{param_name}")
                            )
                        )
                        params[param_name] = f"%{word}%"
                    results = base_query.filter(or_(*conditions)).params(**params).limit(top_k * 2).all()
                    
                    # 相关性过滤
                    results = self._filter_by_relevance(results, query, top_k)
            
            return self._format_search_results(results, query, "keyword")
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    def _semantic_search(self, query: str, top_k: int, filters: Optional[Dict] = None) -> List[Dict]:
        """语义搜索 - 使用原生 SQL 避免 SQLAlchemy 向量方法"""
        if not self.embedding_service.is_enabled():
            logger.warning("Semantic search requested but embedding service not available")
            return []
        
        try:
            # 获取查询向量
            query_embedding = self.embedding_service.get_embedding(query)
            if not query_embedding:
                logger.warning("Failed to get query embedding")
                return []
            
            # 使用 SQLAlchemy 的原生 SQL 执行，但避免 ORM 方法
            from sqlalchemy import text
            
            # 将向量转换为字符串格式
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # 检查有多少 chunks 有向量
            count_sql = text("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
            chunk_count = self.db.execute(count_sql).scalar()
            
            if chunk_count == 0:
                logger.warning("No chunks with embeddings found")
                return []
            
            # 构建语义搜索 SQL
            base_sql = f"""
                SELECT 
                    chunks.id as chunk_id,
                    chunks.text,
                    chunks.chunk_type,
                    contents.id as content_id,
                    contents.title,
                    contents.source_uri,
                    contents.modality,
                    contents.category,
                    contents.tags,
                    contents.created_at,
                    categories.name as category_name,
                    categories.color as category_color,
                    content_categories.confidence as category_confidence,
                    (chunks.embedding <=> '{embedding_str}'::vector) as distance
                FROM chunks 
                JOIN contents ON chunks.content_id = contents.id
                LEFT JOIN content_categories ON contents.id = content_categories.content_id
                LEFT JOIN categories ON content_categories.category_id = categories.id
                WHERE chunks.embedding IS NOT NULL
            """
            
            # 添加过滤条件
            where_conditions = []
            params = {}
            
            if filters:
                if filters.get('modality'):
                    where_conditions.append("contents.modality = %(modality)s")
                    params['modality'] = filters['modality']
                if filters.get('category'):
                    # 支持按分类ID或分类名称筛选
                    category_value = filters['category']
                    if isinstance(category_value, str) and len(category_value) == 36:  # UUID格式
                        where_conditions.append("categories.id = %(category)s")
                    else:
                        where_conditions.append("categories.name = %(category)s")
                    params['category'] = category_value
                if filters.get('created_by'):
                    where_conditions.append("contents.created_by = %(created_by)s")
                    params['created_by'] = filters['created_by']
            
            if where_conditions:
                base_sql += " AND " + " AND ".join(where_conditions)
            
            # 添加相似度阈值过滤（距离小于0.8，即相似度大于0.2）
            base_sql += f"""
                AND (chunks.embedding <=> '{embedding_str}'::vector) < 0.8
                ORDER BY chunks.embedding <=> '{embedding_str}'::vector
                LIMIT {top_k * 2}
            """
            
            sql = text(base_sql)
            
            # 执行查询
            if params:
                results = self.db.execute(sql, params).fetchall()
            else:
                results = self.db.execute(sql).fetchall()
            
            # 使用格式化方法应用去重逻辑
            return self._format_semantic_results(results, query)
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def _hybrid_search(self, query: str, top_k: int, filters: Optional[Dict] = None) -> List[Dict]:
        """混合搜索：结合关键词和语义搜索"""
        try:
            # 获取两种搜索结果
            keyword_results = self._keyword_search(query, top_k, filters)
            
            if self.embedding_service.is_enabled():
                semantic_results = self._semantic_search(query, top_k, filters)
            else:
                semantic_results = []
            
            # 结果去重和融合
            merged_results = self._merge_search_results(keyword_results, semantic_results, top_k)
            
            return merged_results
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return []
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """
        提取搜索词，支持中文搜索优化
        """
        terms = [query]  # 原始查询
        
        # 添加常见同义词和变体
        synonyms = {
            '领英': ['LinkedIn', 'linkedin', '领英网'],
            'LinkedIn': ['领英', 'linkedin'],
            'AI': ['人工智能', '人工智慧', 'ai', 'Ai'],
            '人工智能': ['AI', 'ai', '人工智慧'],
            '报告': ['报表', '分析', '研究'],
            '人才': ['人员', '员工', '专业人士'],
        }
        
        for word, variants in synonyms.items():
            if word in query:
                terms.extend(variants)
        
        # 移除重复项
        return list(set(terms))
    
    def _apply_filters(self, query, filters: Dict):
        """应用搜索过滤条件"""
        for key, value in filters.items():
            if key == "modality":
                query = query.filter(Content.modality == value)
            elif key == "created_by":
                query = query.filter(Content.created_by == value)
            elif key == "category":
                # 支持按分类ID或分类名称筛选
                if isinstance(value, str) and len(value) == 36:  # UUID格式
                    # 通过ContentCategory表关联查询
                    query = query.join(ContentCategory).join(Category).filter(Category.id == value)
                else:
                    # 按分类名称查询
                    query = query.join(ContentCategory).join(Category).filter(Category.name == value)
            elif key == "collection_id":
                # 新增：按合集ID筛选
                try:
                    from uuid import UUID
                    collection_uuid = UUID(value) if isinstance(value, str) else value
                    # 通过合集关联的分类来筛选文档
                    collection = self.db.query(Collection).filter(Collection.id == collection_uuid).first()
                    if collection and collection.category_id:
                        query = query.join(ContentCategory).filter(ContentCategory.category_id == collection.category_id)
                    else:
                        logger.warning(f"Collection {value} not found or has no associated category")
                except Exception as e:
                    logger.error(f"Error filtering by collection_id {value}: {e}")
            elif key == "date_from":
                query = query.filter(Content.created_at >= value)
            elif key == "date_to":
                query = query.filter(Content.created_at <= value)
        return query
    
    def _filter_by_relevance(self, results: List[Tuple], query: str, top_k: int) -> List[Tuple]:
        """基于相关性过滤结果"""
        filtered_results = []
        q_lower = query.lower()
        
        for chunk, content in results:
            text_lower = chunk.text.lower()
            title_lower = content.title.lower()
            
            # 检查词边界匹配
            if (re.search(rf'\\b{re.escape(q_lower)}\\b', text_lower) or
                re.search(rf'\\b{re.escape(q_lower)}\\b', title_lower)):
                filtered_results.append((chunk, content))
            elif len(filtered_results) < top_k:
                # 部分匹配
                if q_lower in text_lower or q_lower in title_lower:
                    filtered_results.append((chunk, content))
            
            if len(filtered_results) >= top_k:
                break
        
        return filtered_results
    
    def _format_search_results(self, results: List[Tuple], query: str, match_type: str) -> List[Dict]:
        """格式化搜索结果"""
        formatted_results = []
        seen_content_ids = {}  # 用于去重，存储 content_id -> 最佳结果
        q_lower = query.lower()
        
        for result in results:
            # 处理不同的结果格式
            if len(result) == 5:  # 包含分类信息
                chunk, content, category_name, category_color, category_confidence = result
            else:  # 只有chunk和content
                chunk, content = result[:2]
                category_name = category_color = category_confidence = None
            
            # 计算相关性分数
            score = self._calculate_relevance_score(chunk.text, content.title, q_lower)
            
            current_result = {
                "score": score,
                "text": chunk.text,
                "title": content.title,
                "content_id": str(content.id),
                "chunk_id": str(chunk.id),
                "source_uri": content.source_uri,
                "modality": content.modality,
                "category": content.category,
                "category_name": category_name,
                "category_color": category_color,
                "category_confidence": float(category_confidence) if category_confidence else None,
                "tags": content.tags,
                "created_at": content.created_at.isoformat(),
                "match_type": match_type,
                "chunk_type": chunk.chunk_type
            }
            
            # 去重逻辑：同一文档只保留得分最高的chunk
            content_id = str(content.id)
            if content_id not in seen_content_ids or current_result["score"] > seen_content_ids[content_id]["score"]:
                seen_content_ids[content_id] = current_result
        
        # 提取去重后的结果
        formatted_results = list(seen_content_ids.values())
        
        # 按分数排序
        formatted_results.sort(key=lambda x: x["score"], reverse=True)
        return formatted_results
    
    def _format_semantic_results(self, results: List[Tuple], query: str) -> List[Dict]:
        """格式化语义搜索结果"""
        formatted_results = []
        seen_content_ids = {}  # 用于去重，存储 content_id -> 最佳结果
        
        # 智能确定相似度阈值和文件类型过滤
        similarity_threshold = self._get_dynamic_similarity_threshold(query)
        expected_modality = self._infer_expected_modality(query)
        
        for row in results:
            # 处理原生 SQL 查询结果
            distance = float(row.distance)
            similarity = 1 - distance  # 转换为相似度分数
            
            # 动态相似度过滤
            if similarity < similarity_threshold:
                continue
            
            # 文件类型智能过滤
            if not self._is_modality_match(query, row.modality, expected_modality, similarity):
                continue
            
            current_result = {
                "score": similarity,
                "text": row.text,
                "title": row.title,
                "content_id": str(row.content_id),
                "chunk_id": str(row.chunk_id),
                "source_uri": row.source_uri,
                "modality": row.modality,
                "category": row.category,
                "category_name": getattr(row, 'category_name', None),
                "category_color": getattr(row, 'category_color', None),
                "category_confidence": float(getattr(row, 'category_confidence', 0)) if getattr(row, 'category_confidence', None) else None,
                "tags": row.tags,
                "created_at": row.created_at.isoformat(),
                "match_type": "semantic",
                "chunk_type": row.chunk_type,
                "distance": distance
            }
            
            # 去重逻辑：同一文档只保留得分最高的chunk
            content_id = str(row.content_id)
            if content_id not in seen_content_ids or current_result["score"] > seen_content_ids[content_id]["score"]:
                seen_content_ids[content_id] = current_result
        
        # 提取去重后的结果
        formatted_results = list(seen_content_ids.values())
        
        # 按分数排序
        formatted_results.sort(key=lambda x: x["score"], reverse=True)
        return formatted_results
    
    def _merge_search_results(self, keyword_results: List[Dict], semantic_results: List[Dict], top_k: int) -> List[Dict]:
        """合并关键词和语义搜索结果（基于文档级别去重）"""
        merged = {}
        
        # 添加关键词结果（权重 0.6）
        for result in keyword_results:
            content_id = result["content_id"]
            result["score"] *= 0.6
            merged[content_id] = result
        
        # 添加语义结果（权重 0.4）
        for result in semantic_results:
            content_id = result["content_id"]
            if content_id in merged:
                # 合并分数，保留更好的chunk信息
                new_score = merged[content_id]["score"] + result["score"] * 0.4
                if result["score"] * 0.4 > merged[content_id]["score"]:
                    # 如果语义搜索的chunk得分更高，使用语义搜索的chunk内容
                    result["score"] = new_score
                    result["match_type"] = "hybrid"
                    merged[content_id] = result
                else:
                    # 否则只更新分数和匹配类型
                    merged[content_id]["score"] = new_score
                    merged[content_id]["match_type"] = "hybrid"
            else:
                result["score"] *= 0.4
                merged[content_id] = result
        
        # 排序并返回
        final_results = list(merged.values())
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:top_k]
    
    def _calculate_relevance_score(self, text: str, title: str, query: str) -> float:
        """计算相关性分数"""
        text_lower = text.lower()
        title_lower = title.lower()
        
        # 精确匹配得分更高
        if re.search(rf'\\b{re.escape(query)}\\b', text_lower):
            return 0.95
        elif re.search(rf'\\b{re.escape(query)}\\b', title_lower):
            return 0.90
        elif query in text_lower:
            return 0.70
        elif query in title_lower:
            return 0.65
        else:
            return 0.50
    
    def _update_search_stats(self, query: str, result_count: int):
        """更新搜索统计"""
        try:
            # 这里可以记录搜索日志，用于分析和优化
            logger.info(f"Search: '{query}' -> {result_count} results")
        except Exception as e:
            logger.error(f"Error updating search stats: {e}")
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """获取热门搜索"""
        # TODO: 实现基于搜索历史的热门搜索
        return []
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """获取搜索建议"""
        try:
            # 基于内容标题和标签生成建议
            suggestions = self.db.query(Content.title).filter(
                Content.title.ilike(f"%{partial_query}%")
            ).limit(limit).all()
            
            return [s[0] for s in suggestions]
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def search_by_category(self, category_identifier: str, query: Optional[str] = None, top_k: int = 20) -> Dict:
        """
        按分类搜索内容
        
        Args:
            category_identifier: 分类ID或分类名称
            query: 可选的搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        try:
            # 获取分类信息 - 支持按ID或名称查找
            category = None
            
            # 首先尝试按UUID查找
            if len(category_identifier) == 36:  # UUID格式
                try:
                    from uuid import UUID
                    uuid_obj = UUID(category_identifier)
                    category = self.db.query(Category).filter(Category.id == uuid_obj).first()
                except ValueError:
                    pass
            
            # 如果按UUID未找到，尝试按名称查找
            if not category:
                category = self.db.query(Category).filter(Category.name == category_identifier).first()
            
            if not category:
                return {
                    "error": f"Category '{category_identifier}' not found",
                    "results": [],
                    "total": 0,
                    "category_identifier": category_identifier
                }
            
            # 构建查询
            base_query = self.db.query(
                Chunk, Content, Category.name.label('category_name'),
                Category.color.label('category_color'),
                ContentCategory.confidence.label('category_confidence')
            ).select_from(Chunk).join(
                Content, Chunk.content_id == Content.id
            ).join(
                ContentCategory, Content.id == ContentCategory.content_id
            ).join(
                Category, ContentCategory.category_id == Category.id
            ).filter(
                Category.id == category.id
            )
            
            # 如果有搜索查询，添加文本匹配
            if query:
                base_query = base_query.filter(
                    or_(
                        Chunk.text.ilike(f"%{query}%"),
                        Content.title.ilike(f"%{query}%")
                    )
                )
            
            # 按置信度和创建时间排序
            results = base_query.order_by(
                desc(ContentCategory.confidence),
                desc(Content.created_at)
            ).limit(top_k).all()
            
            # 格式化结果
            formatted_results = self._format_search_results(results, query or "", "category")
            
            return {
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                    "description": category.description,
                    "color": category.color
                },
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Error searching by category {category_identifier}: {e}")
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "category_identifier": category_identifier
            }
    
    def get_category_stats(self) -> Dict:
        """获取分类统计信息用于搜索 - 只返回系统预置的智能分类"""
        try:
            # 使用高效的SQL聚合查询获取分类统计
            from sqlalchemy import func
            
            # 查询所有系统分类及其内容数量（包括没有内容的分类）
            all_system_categories = self.db.query(Category).filter(
                Category.is_system.is_(True)
            ).all()
            
            category_stats = []
            for category in all_system_categories:
                # 统计该分类下有Chunk的Content数量（与搜索逻辑一致）
                content_count = self.db.query(func.count(func.distinct(Content.id))).select_from(
                    ContentCategory
                ).join(
                    Content, ContentCategory.content_id == Content.id
                ).join(
                    Chunk, Content.id == Chunk.content_id
                ).filter(
                    ContentCategory.category_id == category.id
                ).scalar() or 0
                
                category_stats.append({
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'color': category.color,
                    'is_system': category.is_system,
                    'content_count': content_count
                })
            
            result_categories = []
            for stat in category_stats:
                result_categories.append({
                    "id": str(stat['id']),
                    "name": stat['name'],
                    "color": stat['color'],
                    "is_system": stat['is_system'],
                    "content_count": stat['content_count']
                })
            
            return {
                "categories": result_categories
            }
            
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return {"categories": []}
    
    def _get_dynamic_similarity_threshold(self, query: str) -> float:
        """根据查询内容动态确定相似度阈值"""
        query_lower = query.lower()
        
        # 图片相关查询需要更高的阈值
        image_keywords = ['照片', '图片', '图像', '拍照', '摄影', '风景', '山顶', '海边', '建筑']
        if any(keyword in query_lower for keyword in image_keywords):
            return 0.35  # 图片查询要求更高相似度
        
        # 专业术语查询
        technical_keywords = ['机器学习', '人工智能', '深度学习', '算法', '技术', '编程', '开发']
        if any(keyword in query_lower for keyword in technical_keywords):
            return 0.28  # 技术查询稍微宽松一些
        
        # 一般查询
        return 0.25
    
    def _infer_expected_modality(self, query: str) -> str:
        """推断查询期望的文件类型"""
        query_lower = query.lower()
        
        # 图片相关关键词
        image_keywords = ['照片', '图片', '图像', '拍照', '摄影', '风景', '山顶', '海边', '建筑', '人像']
        if any(keyword in query_lower for keyword in image_keywords):
            return 'image'
        
        # PDF文档关键词
        pdf_keywords = ['报告', '文档', '论文', '研究', '分析', '白皮书']
        if any(keyword in query_lower for keyword in pdf_keywords):
            return 'pdf'
        
        # 返回空表示不限制文件类型
        return ''
    
    def _is_modality_match(self, query: str, file_modality: str, expected_modality: str, similarity: float) -> bool:
        """检查文件类型是否匹配查询意图"""
        # 如果没有明确的文件类型期望，允许所有类型
        if not expected_modality:
            return True
        
        # 如果期望的类型与实际类型匹配
        if expected_modality == file_modality:
            return True
        
        # 如果相似度非常高（>0.4），允许跨类型匹配
        if similarity > 0.4:
            return True
        
        # 特殊情况：图片查询但文件是文本，需要更高的相似度
        if expected_modality == 'image' and file_modality in ['text', 'pdf']:
            return similarity > 0.45  # 需要非常高的相似度才允许
        
        return False
