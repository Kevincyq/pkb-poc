"""
问答服务 - 基于检索增强生成 (RAG)
使用 Turing 平台 API 调用 OpenAI 模型
"""
import os
import time
import uuid
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import QAHistory, Content, Chunk
from app.services.search_service import SearchService
import logging

# 导入新版本 OpenAI 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.search_service = SearchService(db, user_id)
        
        # 检查 OpenAI 库可用性
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available. Install with: pip install openai>=1.0.0")
            self.openai_enabled = False
            self.openai_client = None
            return
        
        # 配置 Turing API
        self.turing_api_key = os.getenv("TURING_API_KEY")
        self.turing_api_base = os.getenv("TURING_API_BASE")
        self.qa_model = os.getenv("QA_MODEL", "turing/gpt-4o-mini")
        
        # 检查必要的环境变量
        if not self.turing_api_key or not self.turing_api_base:
            logger.error("Turing API configuration missing. Please set TURING_API_KEY and TURING_API_BASE")
            self.openai_enabled = False
            self.openai_client = None
            return
        
        try:
            # 创建 Turing API 客户端
            self.openai_client = OpenAI(
                api_key=self.turing_api_key,
                base_url=self.turing_api_base
            )
            self.openai_enabled = True
            logger.info(f"Turing API client initialized successfully with model: {self.qa_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Turing API client: {e}")
            self.openai_enabled = False
            self.openai_client = None
    
    def is_enabled(self) -> bool:
        """检查 QA 服务是否可用"""
        return self.openai_enabled and self.openai_client is not None
    
    def test_connection(self) -> Dict:
        """测试 Turing API 连接"""
        if not self.openai_client:
            return {
                "status": "error",
                "message": "Turing API 客户端未配置"
            }
        
        try:
            # 发送测试请求
            response = self.openai_client.chat.completions.create(
                model=self.qa_model,
                messages=[
                    {"role": "system", "content": "你是一个礼貌的 AI 助手，你叫 '小T'。"},
                    {"role": "user", "content": "请简单回应一下，确认连接正常"}
                ],
                max_tokens=20,
                temperature=0.7
            )
            
            return {
                "status": "success",
                "message": "Turing API 连接正常",
                "model": self.qa_model,
                "test_response": response.choices[0].message.content
            }
        except Exception as e:
            logger.error(f"Turing API connection test failed: {e}")
            return {
                "status": "error",
                "message": f"Turing API 连接失败: {str(e)}"
            }
    
    def ask(
        self, 
        question: str, 
        session_id: Optional[str] = None,
        context_limit: int = 3000,
        model: Optional[str] = None,
        search_type: str = "hybrid",
        category_filter: Optional[str] = None,
        collection_id: Optional[str] = None
    ) -> Dict:
        """
        基于知识库的问答
        
        Args:
            question: 用户问题
            session_id: 会话ID（用于上下文）
            context_limit: 上下文字符限制
            model: 使用的LLM模型
            search_type: 搜索类型
            category_filter: 分类筛选（分类ID或名称）
            collection_id: 合集范围限制（合集ID）
        
        Returns:
            问答结果字典
        """
        if not self.openai_enabled:
            return self._fallback_answer(question)
        
        # 使用配置的模型或传入的模型
        if model is None:
            model = self.qa_model
        
        try:
            # 1. 搜索相关文档
            # 构建搜索过滤条件
            filters = {}
            if category_filter:
                filters["category"] = category_filter
            
            # 如果指定了合集范围，限制搜索范围
            if collection_id:
                filters["collection_id"] = collection_id
            
            logger.info(f"🔍 QA searching: question='{question}', search_type={search_type}, filters={filters}")
            search_results = self.search_service.search(
                query=question, 
                top_k=5, 
                search_type=search_type,
                filters=filters if filters else None
            )
            logger.info(f"📊 QA search returned: {search_results.get('total', 0)} results")
            
            if not search_results["results"]:
                return {
                    "question": question,
                    "answer": "抱歉，我在知识库中没有找到相关信息来回答您的问题。",
                    "sources": [],
                    "formatted_sources": "",
                    "confidence": 0.0,
                    "session_id": session_id
                }
            
            # 2. 构建上下文
            logger.info(f"📚 Building context from {len(search_results['results'])} search results")
            context, sources = self._build_context(search_results["results"], context_limit)
            logger.info(f"📚 Context built: {len(sources)} unique documents, context length: {len(context)} chars")
            
            # 3. 获取历史对话（如果有会话ID）
            conversation_history = self._get_conversation_history(session_id) if session_id else []
            
            # 4. 过滤高质量来源
            filtered_sources = self._filter_high_quality_sources(sources, question)
            
            # 如果过滤后没有高质量来源，但原始搜索有结果，给出提示
            if not filtered_sources and sources:
                logger.warning(f"No high-quality sources found for question: {question}")
                return {
                    "question": question,
                    "answer": "抱歉，虽然找到了一些相关文档，但相关度较低，无法为您提供准确的答案。建议您尝试使用更具体的关键词重新提问。",
                    "sources": [],
                    "formatted_sources": "",
                    "confidence": 0.1,
                    "session_id": session_id
                }
            
            # 5. 生成格式化的文档来源信息
            formatted_sources = self._format_sources_for_display(filtered_sources)
            
            # 6. 生成回答
            answer_data = self._generate_answer(question, context, conversation_history, model, category_filter, formatted_sources)
            
            # 7. 保存问答历史
            qa_record = self._save_qa_history(
                question=question,
                answer=answer_data["answer"],
                sources=filtered_sources,
                session_id=session_id,
                model_used=model,
                tokens_used=answer_data.get("tokens_used", 0),
                confidence=answer_data.get("confidence", 0.0)
            )
            
            return {
                "question": question,
                "answer": answer_data["answer"],
                "sources": filtered_sources,  # 返回过滤后的来源（原始数据）
                "formatted_sources": formatted_sources,  # 格式化的来源信息
                "confidence": answer_data.get("confidence", 0.0),
                "model_used": model,
                "search_type": search_type,
                "category_filter": category_filter,
                "session_id": session_id,
                "qa_id": str(qa_record.id),
                "search_results_count": len(search_results["results"])
            }
            
        except Exception as e:
            logger.error(f"QA service error: {e}")
            return {
                "question": question,
                "answer": f"生成回答时出错：{str(e)}",
                "sources": [],
                "confidence": 0.0,
                "session_id": session_id,
                "error": str(e)
            }
    
    def _build_context(self, search_results: List[Dict], limit: int) -> Tuple[str, List[Dict]]:
        """构建上下文和来源信息（文档级别去重，保留最高分）"""
        seen_content_ids = {}  # 用于去重，跟踪已添加的最佳文档
        
        # 第一次遍历：去重并保留每个文档得分最高的chunk
        for result in search_results:
            content_id = result["content_id"]
            
            # 去重：同一文档保留得分最高的chunk
            if content_id in seen_content_ids:
                existing_result = seen_content_ids[content_id]
                if result["score"] > existing_result["score"]:
                    # 替换为更高分的chunk
                    logger.debug(f"Replacing {result['title']} with better score: {existing_result['score']:.3f} -> {result['score']:.3f}")
                    seen_content_ids[content_id] = result
            else:
                # 标记该文档已被添加
                seen_content_ids[content_id] = result
        
        # 按分数排序去重后的结果
        unique_results = list(seen_content_ids.values())
        unique_results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"🔄 Deduplication: {len(search_results)} chunks -> {len(unique_results)} unique docs")
        for i, result in enumerate(unique_results[:3]):
            logger.info(f"  Doc {i+1}: {result['title'][:50]} (score: {result['score']:.3f})")
        
        # 第二次遍历：构建上下文和来源信息
        context_parts = []
        sources = []
        current_length = 0
        
        for i, result in enumerate(unique_results):
            doc_number = i + 1
            source_info = f"[文档{doc_number}: {result['title']}]"
            content = f"{source_info}\\n{result['text']}\\n"
            
            if current_length + len(content) > limit:
                logger.info(f"⚠️ Context limit reached at document {doc_number}/{len(unique_results)}")
                break
            
            context_parts.append(content)
            current_length += len(content)
            
            # 添加来源信息
            sources.append({
                "title": result["title"],
                "text": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                "source_uri": result["source_uri"],
                "score": result["score"],
                "content_id": result["content_id"],
                "category_name": result.get("category_name"),
                "modality": result.get("modality", "text"),
                "confidence_percentage": round(result["score"] * 100, 0) if result["score"] else 0
            })
        
        context = "\\n".join(context_parts)
        logger.info(f"✅ Final context: {len(sources)} docs, {len(context)} chars")
        return context, sources
    
    def _filter_high_quality_sources(self, sources: List[Dict], question: str) -> List[Dict]:
        """过滤高质量的文档来源"""
        if not sources:
            return []
        
        # 设置相关度阈值
        min_score_threshold = 0.15  # 最低相关度阈值（降低到15%）
        high_score_threshold = 0.5   # 高相关度阈值（降低到50%）
        
        # 分析问题关键词
        question_lower = question.lower()
        question_keywords = self._extract_question_keywords(question_lower)
        
        logger.info(f"Question: {question}")
        logger.info(f"Extracted keywords: {question_keywords}")
        logger.info(f"Original sources count: {len(sources)}")
        
        filtered_sources = []
        
        for source in sources:
            score = source.get("score", 0)
            title = source.get("title", "").lower()
            text = source.get("text", "").lower()
            
            # 基础相关度过滤
            if score < min_score_threshold:
                continue
            
            # 关键词匹配检查
            keyword_matches = 0
            for keyword in question_keywords:
                if keyword in title or keyword in text:
                    keyword_matches += 1
            
            # 计算综合相关度
            keyword_ratio = keyword_matches / len(question_keywords) if question_keywords else 0
            combined_score = score * 0.7 + keyword_ratio * 0.3
            
            # 更新相关度百分比
            source["confidence_percentage"] = round(combined_score * 100, 0)
            
            # 检查是否为图片搜索
            is_image_search = any(keyword in question_lower for keyword in ['照片', '图片', '图像', '拍照', '摄影'])
            
            # 高质量来源：高相关度或关键词匹配度高
            if combined_score >= high_score_threshold or keyword_ratio >= 0.4:
                filtered_sources.append(source)
            # 中等质量来源：如果已有来源少于3个，可以包含
            elif len(filtered_sources) < 3 and combined_score >= min_score_threshold:
                filtered_sources.append(source)
            # 图片搜索特殊处理：更宽松的阈值，因为同类图片都有价值
            elif is_image_search and len(filtered_sources) < 3 and score >= 0.1:
                filtered_sources.append(source)
            # 低质量但仍有一定相关性的来源：如果没有其他来源，至少保留一个
            elif len(filtered_sources) == 0 and score >= 0.1:
                filtered_sources.append(source)
        
        # 按综合相关度排序
        filtered_sources.sort(key=lambda x: x.get("confidence_percentage", 0), reverse=True)
        
        logger.info(f"Filtered sources count: {len(filtered_sources)}")
        for i, source in enumerate(filtered_sources):
            logger.info(f"Source {i+1}: {source.get('title', 'Unknown')} - {source.get('confidence_percentage', 0)}%")
        
        # 最多返回3个，但需要智能判断是否过滤
        max_sources = 3
        if len(filtered_sources) > 1:
            # 检查是否为图片搜索（根据问题内容判断）
            is_image_search = any(keyword in question.lower() for keyword in ['照片', '图片', '图像', '拍照', '摄影'])
            
            # 检查第二个来源的质量，如果相关度差距太大，只返回第一个
            first_score = filtered_sources[0].get("confidence_percentage", 0)
            second_score = filtered_sources[1].get("confidence_percentage", 0)
            
            # 图片搜索使用更宽松的阈值，因为同类图片相关度通常比较接近
            threshold = 30 if is_image_search else 50
            
            if first_score - second_score > threshold:
                logger.info(f"Filtering out low-quality sources (threshold={threshold}%): first={first_score}%, second={second_score}%")
                return filtered_sources[:1]
        
        final_sources = filtered_sources[:max_sources]
        logger.info(f"Final sources count: {len(final_sources)}")
        
        return final_sources
    
    def _extract_question_keywords(self, question: str) -> List[str]:
        """提取问题中的关键词"""
        # 移除常见的疑问词和停用词
        stop_words = {
            "什么", "哪些", "如何", "怎么", "为什么", "谁", "哪个", "哪里", "什么时候", 
            "有", "是", "的", "了", "在", "和", "与", "或", "但是", "然而", "因为",
            "所以", "这个", "那个", "这些", "那些", "我", "你", "他", "她", "它们",
            "任务", "项目", "工作", "会议", "问题"  # 添加一些通用词
        }
        
        # 简单分词（按空格和标点分割）
        import re
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', question)
        
        # 过滤停用词，但保留人名（通常2-4个字符）
        keywords = []
        for word in words:
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word)
            # 特殊处理：如果是可能的人名（2-4个字符的中文），即使在停用词中也保留
            elif len(word) >= 2 and len(word) <= 4 and re.match(r'^[\u4e00-\u9fff]+$', word):
                # 检查是否包含常见姓氏
                common_surnames = {'张', '王', '李', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗'}
                if any(word.startswith(surname) for surname in common_surnames):
                    keywords.append(word)
        
        return keywords
    
    def _format_sources_for_display(self, sources: List[Dict]) -> str:
        """格式化文档来源信息为Markdown格式"""
        if not sources:
            return ""
        
        formatted_lines = ["### 🔗 相关文档"]
        
        for i, source in enumerate(sources, 1):
            title = source.get("title", "未知文档")
            category_name = source.get("category_name", "")
            confidence = source.get("confidence_percentage", 0)
            content_id = source.get("content_id", "")
            
            # 生成内部链接URL（前端会处理这个链接）
            if category_name:
                link_url = f"#/collection/{category_name}?highlight={content_id}"
            else:
                link_url = f"#/document/{content_id}"
            
            # 格式化每个文档条目
            formatted_lines.append(f"{i}. [{title}]({link_url}) - 相关度：{confidence}%")
        
        return "\n".join(formatted_lines)
    
    def _get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """获取对话历史"""
        try:
            history = self.db.query(QAHistory).filter(
                QAHistory.session_id == session_id
            ).order_by(QAHistory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "question": h.question,
                    "answer": h.answer,
                    "created_at": h.created_at.isoformat()
                }
                for h in reversed(history)  # 按时间正序
            ]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _build_conversation_messages(
        self, 
        question: str, 
        context: str, 
        conversation_history: List[Dict],
        category_filter: Optional[str] = None,
        formatted_sources: str = ""
    ) -> List[Dict]:
        """构建包含多轮对话历史的消息列表"""
        messages = []
        
        # 1. 系统提示
        system_prompt = self._build_system_prompt(category_filter)
        messages.append({"role": "system", "content": system_prompt})
        
        # 2. 添加对话历史（最近的几轮）
        for hist in conversation_history[-6:]:  # 保留最近6轮对话
            messages.append({"role": "user", "content": hist["question"]})
            messages.append({"role": "assistant", "content": hist["answer"]})
        
        # 3. 当前问题和上下文
        current_message = self._build_user_message(question, context, [], formatted_sources)
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _generate_answer(
        self, 
        question: str, 
        context: str, 
        conversation_history: List[Dict],
        model: str,
        category_filter: Optional[str] = None,
        formatted_sources: str = ""
    ) -> Dict:
        """生成回答 - 使用 Turing API 和多轮对话"""
        if not self.openai_client:
            return {
                "answer": "Turing API 客户端未配置，无法生成回答。",
                "confidence": 0.0,
                "tokens_used": 0
            }
        
        try:
            # 构建消息列表，包含多轮对话历史
            messages = self._build_conversation_messages(question, context, conversation_history, category_filter, formatted_sources)
            
            logger.info(f"Generating answer using model: {model}")
            logger.debug(f"Message count: {len(messages)}")
            
            # 调用 Turing API
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Answer generated successfully, tokens used: {tokens_used}")
            
            # 计算置信度（基于答案长度和搜索结果相关性）
            confidence = self._calculate_confidence(answer, context)
            
            return {
                "answer": answer,
                "confidence": confidence,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"Error generating answer with Turing API: {e}")
            return {
                "answer": f"生成回答时出错：{str(e)}",
                "confidence": 0.0,
                "tokens_used": 0
            }
    
    def _build_system_prompt(self, category_filter: Optional[str] = None) -> str:
        """构建系统提示"""
        base_prompt = """你是一个专业的个人知识库助手。请基于提供的文档内容回答用户问题。

回答格式要求：
请使用以下结构化的Markdown格式回答：

## 📋 关于您的问题

### 💡 核心答案
[在这里提供简洁明确的核心答案]

### 📚 详细说明
- **要点1**：具体说明内容
- **要点2**：具体说明内容
- **要点3**：具体说明内容

### 💭 补充信息
[如有需要，提供补充说明或相关背景信息]

规则：
1. 严格按照上述Markdown格式输出
2. 只基于提供的文档内容回答，不要添加文档中没有的信息
3. 如果文档中信息不足以回答问题，请在"核心答案"部分诚实说明
4. 回答要准确、简洁、有条理
5. 可以在详细说明中引用具体的文档内容
6. 使用中文回答"""

        if category_filter:
            base_prompt += f"""
7. 当前查询限定在"{category_filter}"分类范围内，请在回答时考虑这个上下文"""

        return base_prompt
    
    def _build_user_message(self, question: str, context: str, conversation_history: List[Dict], formatted_sources: str = "") -> str:
        """构建用户消息"""
        message_parts = []
        
        # 添加对话历史
        if conversation_history:
            message_parts.append("对话历史：")
            for h in conversation_history[-3:]:  # 只保留最近3轮对话
                message_parts.append(f"Q: {h['question']}")
                message_parts.append(f"A: {h['answer'][:100]}...")  # 截断历史回答
            message_parts.append("")
        
        # 添加文档上下文
        message_parts.append("相关文档内容：")
        message_parts.append(context)
        message_parts.append("")
        
        # 添加当前问题
        message_parts.append(f"用户问题：{question}")
        message_parts.append("")
        message_parts.append("请基于上述文档内容回答用户问题。")
        
        # 如果有格式化的来源信息，提示AI在回复末尾添加
        if formatted_sources:
            message_parts.append("")
            message_parts.append("注意：请在你的回复末尾添加以下文档来源信息：")
            message_parts.append(formatted_sources)
        
        return "\\n".join(message_parts)
    
    def _calculate_confidence(self, answer: str, context: str) -> float:
        """计算回答置信度"""
        try:
            # 简单的置信度计算逻辑
            if "抱歉" in answer or "不知道" in answer or "没有找到" in answer:
                return 0.2
            elif len(answer) < 50:
                return 0.5
            elif len(context) > 1000:
                return 0.9
            else:
                return 0.7
        except:
            return 0.5
    
    def _save_qa_history(
        self, 
        question: str, 
        answer: str, 
        sources: List[Dict],
        session_id: Optional[str],
        model_used: str,
        tokens_used: int,
        confidence: float
    ) -> QAHistory:
        """保存问答历史"""
        try:
            qa_record = QAHistory(
                user_id=self.user_id,  # ✅ 添加用户隔离
                session_id=session_id,
                question=question,
                answer=answer,
                sources=[{"content_id": s["content_id"], "title": s["title"]} for s in sources],
                model_used=model_used,
                tokens_used=tokens_used,
                confidence=confidence
            )
            
            self.db.add(qa_record)
            self.db.commit()
            self.db.refresh(qa_record)
            
            return qa_record
            
        except Exception as e:
            logger.error(f"Error saving QA history: {e}")
            self.db.rollback()
            # 返回一个临时对象
            temp_record = QAHistory(id=uuid.uuid4())
            return temp_record
    
    def _fallback_answer(self, question: str) -> Dict:
        """当 OpenAI 不可用时的回退回答"""
        return {
            "question": question,
            "answer": "抱歉，AI 问答服务当前不可用。您可以尝试使用搜索功能查找相关信息。",
            "sources": [],
            "confidence": 0.0,
            "model_used": "fallback"
        }
    
    def get_qa_history(self, session_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """获取问答历史"""
        try:
            query = self.db.query(QAHistory)
            
            # ✅ 添加用户隔离
            if self.user_id:
                query = query.filter(QAHistory.user_id == self.user_id)
            
            if session_id:
                query = query.filter(QAHistory.session_id == session_id)
            
            history = query.order_by(QAHistory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": str(h.id),
                    "question": h.question,
                    "answer": h.answer,
                    "confidence": h.confidence,
                    "model_used": h.model_used,
                    "created_at": h.created_at.isoformat(),
                    "sources_count": len(h.sources) if h.sources else 0
                }
                for h in history
            ]
            
        except Exception as e:
            logger.error(f"Error getting QA history: {e}")
            return []
    
    def update_feedback(self, qa_id: str, feedback: str) -> bool:
        """更新问答反馈"""
        try:
            qa_record = self.db.query(QAHistory).filter(QAHistory.id == qa_id).first()
            if qa_record:
                qa_record.feedback = feedback
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating feedback: {e}")
            return False
