"""
Agent 服务框架
支持任务规划、工具调用和执行
"""
import json
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models import AgentTask, MCPTool
from app.services.qa_service import QAService
from app.services.search_service import SearchService
import logging

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.qa_service = QAService(db)
        self.search_service = SearchService(db)
        self.available_tools = self._load_available_tools()
    
    def execute_task(
        self, 
        task_type: str, 
        input_data: Dict, 
        agent_name: str = "default"
    ) -> Dict:
        """
        执行 Agent 任务
        
        Args:
            task_type: 任务类型 (memo, email, calendar, todo, search, qa)
            input_data: 输入数据
            agent_name: Agent 名称
        
        Returns:
            执行结果
        """
        try:
            # 创建任务记录
            task = AgentTask(
                task_type=task_type,
                input_data=input_data,
                status="running",
                agent_used=agent_name
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            # 执行任务
            result = self._execute_task_by_type(task_type, input_data, str(task.id))
            
            # 更新任务状态
            task.output_data = result
            task.status = "completed" if result.get("success", False) else "failed"
            task.tools_used = result.get("tools_used", [])
            task.execution_log = result.get("execution_log", "")
            self.db.commit()
            
            return {
                "task_id": str(task.id),
                "status": task.status,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Agent task execution error: {e}")
            if 'task' in locals():
                task.status = "failed"
                task.execution_log = str(e)
                self.db.commit()
            
            return {
                "task_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    def _execute_task_by_type(self, task_type: str, input_data: Dict, task_id: str) -> Dict:
        """根据任务类型执行具体任务"""
        execution_log = []
        tools_used = []
        
        try:
            if task_type == "search":
                return self._handle_search_task(input_data, execution_log, tools_used)
            
            elif task_type == "qa":
                return self._handle_qa_task(input_data, execution_log, tools_used)
            
            elif task_type == "memo":
                return self._handle_memo_task(input_data, execution_log, tools_used)
            
            elif task_type == "email":
                return self._handle_email_task(input_data, execution_log, tools_used)
            
            elif task_type == "calendar":
                return self._handle_calendar_task(input_data, execution_log, tools_used)
            
            elif task_type == "todo":
                return self._handle_todo_task(input_data, execution_log, tools_used)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown task type: {task_type}",
                    "execution_log": "\\n".join(execution_log),
                    "tools_used": tools_used
                }
                
        except Exception as e:
            execution_log.append(f"Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_log": "\\n".join(execution_log),
                "tools_used": tools_used
            }
    
    def _handle_search_task(self, input_data: Dict, execution_log: List, tools_used: List) -> Dict:
        """处理搜索任务"""
        query = input_data.get("query", "")
        search_type = input_data.get("search_type", "hybrid")
        top_k = input_data.get("top_k", 10)
        
        execution_log.append(f"Executing search: '{query}' (type: {search_type})")
        tools_used.append("search_service")
        
        results = self.search_service.search(query, top_k, search_type)
        
        execution_log.append(f"Found {results['total']} results")
        
        return {
            "success": True,
            "data": results,
            "execution_log": "\\n".join(execution_log),
            "tools_used": tools_used
        }
    
    def _handle_qa_task(self, input_data: Dict, execution_log: List, tools_used: List) -> Dict:
        """处理问答任务"""
        question = input_data.get("question", "")
        session_id = input_data.get("session_id")
        
        execution_log.append(f"Executing QA: '{question}'")
        tools_used.append("qa_service")
        
        result = self.qa_service.ask(question, session_id)
        
        execution_log.append(f"Generated answer with confidence: {result.get('confidence', 0)}")
        
        return {
            "success": True,
            "data": result,
            "execution_log": "\\n".join(execution_log),
            "tools_used": tools_used
        }
    
    def _handle_memo_task(self, input_data: Dict, execution_log: List, tools_used: List) -> Dict:
        """处理备忘录任务"""
        content = input_data.get("content", "")
        title = input_data.get("title", "Agent Memo")
        
        execution_log.append(f"Creating memo: '{title}'")
        tools_used.append("memo_creator")
        
        # TODO: 调用摄取服务创建备忘录
        # 这里可以调用现有的 ingest_memo API
        
        return {
            "success": True,
            "data": {
                "title": title,
                "content": content,
                "created": True
            },
            "execution_log": "\\n".join(execution_log),
            "tools_used": tools_used
        }
    
    def _handle_email_task(self, input_data: Dict, execution_log: List, tools_used: List) -> Dict:
        """处理邮件任务"""
        action = input_data.get("action", "send")  # send, read, search
        
        execution_log.append(f"Email task: {action}")
        tools_used.append("email_tool")
        
        # TODO: 集成邮件服务
        # 这里需要集成 MCP 邮件工具
        
        return {
            "success": False,
            "error": "Email functionality not implemented yet",
            "execution_log": "\\n".join(execution_log),
            "tools_used": tools_used
        }
    
    def _handle_calendar_task(self, input_data: Dict, execution_log: List, tools_used: List) -> Dict:
        """处理日历任务"""
        action = input_data.get("action", "create")  # create, read, update, delete
        
        execution_log.append(f"Calendar task: {action}")
        tools_used.append("calendar_tool")
        
        # TODO: 集成日历服务
        # 这里需要集成 MCP 日历工具
        
        return {
            "success": False,
            "error": "Calendar functionality not implemented yet",
            "execution_log": "\\n".join(execution_log),
            "tools_used": tools_used
        }
    
    def _handle_todo_task(self, input_data: Dict, execution_log: List, tools_used: List) -> Dict:
        """处理待办任务"""
        action = input_data.get("action", "create")  # create, list, update, complete
        
        execution_log.append(f"Todo task: {action}")
        tools_used.append("todo_tool")
        
        # TODO: 集成待办事项管理
        # 可以基于现有的 OpsLog 扩展
        
        return {
            "success": False,
            "error": "Todo functionality not implemented yet",
            "execution_log": "\\n".join(execution_log),
            "tools_used": tools_used
        }
    
    def _load_available_tools(self) -> Dict[str, Dict]:
        """加载可用的工具"""
        try:
            tools = self.db.query(MCPTool).filter(MCPTool.enabled == True).all()
            return {
                tool.name: {
                    "description": tool.description,
                    "category": tool.category,
                    "config": tool.config
                }
                for tool in tools
            }
        except Exception as e:
            logger.error(f"Error loading tools: {e}")
            return {}
    
    def register_tool(self, name: str, description: str, category: str, config: Dict) -> bool:
        """注册新工具"""
        try:
            tool = MCPTool(
                name=name,
                description=description,
                category=category,
                config=config
            )
            self.db.add(tool)
            self.db.commit()
            
            # 重新加载工具列表
            self.available_tools = self._load_available_tools()
            
            return True
        except Exception as e:
            logger.error(f"Error registering tool: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        try:
            task = self.db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                return {
                    "id": str(task.id),
                    "task_type": task.task_type,
                    "status": task.status,
                    "agent_used": task.agent_used,
                    "tools_used": task.tools_used,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
            return None
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return None
    
    def get_available_tools(self) -> Dict[str, Dict]:
        """获取可用工具列表"""
        return self.available_tools
    
    def plan_complex_task(self, user_input: str) -> List[Dict]:
        """
        规划复杂任务
        将用户输入分解为多个子任务
        """
        # TODO: 使用 LLM 进行任务规划
        # 这里可以集成 OpenAI 或其他 LLM 来理解用户意图并规划任务
        
        # 简单的规则基础规划
        tasks = []
        
        if "搜索" in user_input or "查找" in user_input:
            tasks.append({
                "task_type": "search",
                "input_data": {"query": user_input}
            })
        
        if "问题" in user_input or "?" in user_input or "？" in user_input:
            tasks.append({
                "task_type": "qa",
                "input_data": {"question": user_input}
            })
        
        return tasks
