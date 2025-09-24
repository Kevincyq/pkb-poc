"""
问答 API 路由
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.qa_service import QAService
from typing import Optional
from pydantic import BaseModel
import time

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class QARequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    context_limit: int = 3000
    model: str = "turing/gpt-4o-mini"
    search_type: str = "hybrid"
    category_filter: Optional[str] = None
    collection_id: Optional[str] = None  # 新增：合集范围限制

class FeedbackRequest(BaseModel):
    qa_id: str
    feedback: str  # "good" or "bad"

class ReportRequest(BaseModel):
    collection_id: str
    report_type: str = "daily"  # daily, weekly, monthly
    date_range: Optional[str] = "today"  # today, this_week, this_month

@router.post("/ask")
async def ask_question(
    request: QARequest,
    db: Session = Depends(get_db)
):
    """
    智能问答接口
    基于知识库内容生成回答
    """
    qa_service = QAService(db)
    result = qa_service.ask(
        question=request.question,
        session_id=request.session_id,
        context_limit=request.context_limit,
        model=request.model,
        search_type=request.search_type,
        category_filter=request.category_filter,
        collection_id=request.collection_id
    )
    return result

@router.post("/generate-report")
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    基于合集内容生成工作日报
    """
    qa_service = QAService(db)
    
    try:
        # 获取合集信息
        from app.models import Collection
        from uuid import UUID
        
        collection_uuid = UUID(request.collection_id)
        collection = db.query(Collection).filter(Collection.id == collection_uuid).first()
        
        if not collection:
            return {"error": "合集不存在"}
        
        # 获取合集中的文档内容
        from app.models import Content, ContentCategory
        
        contents = db.query(Content).join(ContentCategory).filter(
            ContentCategory.category_id == collection.category_id
        ).all()
        
        if not contents:
            return {"error": "合集中没有文档"}
        
        # 构建日报生成提示
        documents_text = ""
        for content in contents[:10]:  # 限制最多10个文档
            documents_text += f"\n\n=== {content.title} ===\n"
            documents_text += content.text[:500] + "..." if len(content.text) > 500 else content.text
        
        report_prompt = f"""
基于以下{collection.name}的内容，生成一份工作日报：

{documents_text}

请按以下格式生成日报：

## 📋 工作日报 - {collection.name}

### 🎯 主要议题
[总结主要讨论的议题和话题]

### 📌 重要决策
[列出重要的决策和结论]

### ✅ 待办事项
[提取出的行动项和待办事项]

### 📅 下一步计划
[后续的计划和安排]

### 👥 参与人员
[如果有提到参与人员，请列出]

请确保内容简洁明了，重点突出。
"""
        
        # 调用AI生成日报
        if qa_service.is_enabled():
            response = qa_service.openai_client.chat.completions.create(
                model=qa_service.qa_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的工作日报生成助手，擅长从会议纪要和工作文档中提取关键信息。"},
                    {"role": "user", "content": report_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            report_content = response.choices[0].message.content
            
            return {
                "success": True,
                "collection_name": collection.name,
                "report_type": request.report_type,
                "report_content": report_content,
                "source_documents": len(contents),
                "generated_at": time.time()
            }
        else:
            return {"error": "AI服务不可用"}
            
    except Exception as e:
        return {"error": f"生成日报失败: {str(e)}"}

@router.get("/history")
async def get_qa_history(
    session_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取问答历史"""
    qa_service = QAService(db)
    history = qa_service.get_qa_history(session_id, limit)
    
    return {
        "session_id": session_id,
        "history": history,
        "total": len(history)
    }

@router.post("/feedback")
async def update_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """更新问答反馈"""
    qa_service = QAService(db)
    success = qa_service.update_feedback(request.qa_id, request.feedback)
    
    return {
        "success": success,
        "qa_id": request.qa_id,
        "feedback": request.feedback
    }

@router.get("/sessions")
async def get_active_sessions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取活跃会话列表"""
    # TODO: 实现会话管理
    return {
        "sessions": [],
        "message": "Session management not implemented yet"
    }

@router.get("/test")
async def test_qa_service(db: Session = Depends(get_db)):
    """测试 QA 服务配置和 Turing API 连接"""
    qa_service = QAService(db)
    
    return {
        "qa_enabled": qa_service.is_enabled(),
        "connection_test": qa_service.test_connection(),
        "search_enabled": qa_service.search_service.embedding_service.is_enabled(),
        "configured_model": getattr(qa_service, 'qa_model', 'Not configured')
    }
