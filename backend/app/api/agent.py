"""
Agent API 路由
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.agent_service import AgentService
from app.services.mcp_service import MCPService
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AgentTaskRequest(BaseModel):
    task_type: str  # memo, email, calendar, todo, search, qa
    input_data: Dict
    agent_name: str = "default"

class MCPToolRequest(BaseModel):
    name: str
    description: str
    category: str  # connector, executor, reader, writer
    config: Dict

class MCPCallRequest(BaseModel):
    tool_name: str
    parameters: Dict

@router.post("/execute")
async def execute_agent_task(
    request: AgentTaskRequest,
    db: Session = Depends(get_db)
):
    """
    执行 Agent 任务
    """
    agent_service = AgentService(db)
    result = agent_service.execute_task(
        task_type=request.task_type,
        input_data=request.input_data,
        agent_name=request.agent_name
    )
    return result

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    agent_service = AgentService(db)
    status = agent_service.get_task_status(task_id)
    
    if status:
        return status
    else:
        return {"error": "Task not found"}

@router.post("/plan")
async def plan_complex_task(
    user_input: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    规划复杂任务
    将用户输入分解为多个子任务
    """
    agent_service = AgentService(db)
    tasks = agent_service.plan_complex_task(user_input)
    
    return {
        "user_input": user_input,
        "planned_tasks": tasks,
        "task_count": len(tasks)
    }

@router.get("/tools")
async def get_available_tools(db: Session = Depends(get_db)):
    """获取可用工具列表"""
    agent_service = AgentService(db)
    tools = agent_service.get_available_tools()
    
    return {
        "tools": tools,
        "count": len(tools)
    }

# MCP 工具管理
@router.post("/mcp/register")
async def register_mcp_tool(
    request: MCPToolRequest,
    db: Session = Depends(get_db)
):
    """注册 MCP 工具"""
    mcp_service = MCPService(db)
    success = mcp_service.register_tool(
        name=request.name,
        description=request.description,
        category=request.category,
        config=request.config
    )
    
    return {
        "success": success,
        "tool_name": request.name
    }

@router.post("/mcp/call")
async def call_mcp_tool(
    request: MCPCallRequest,
    db: Session = Depends(get_db)
):
    """调用 MCP 工具"""
    mcp_service = MCPService(db)
    result = mcp_service.call_tool(request.tool_name, request.parameters)
    
    return result

@router.get("/mcp/tools")
async def get_mcp_tools(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 MCP 工具列表"""
    mcp_service = MCPService(db)
    
    if category:
        tools = mcp_service.get_tools_by_category(category)
    else:
        tools = mcp_service.get_available_tools()
    
    return {
        "tools": tools,
        "category": category,
        "count": len(tools)
    }

@router.post("/mcp/tools/{tool_name}/enable")
async def enable_mcp_tool(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """启用 MCP 工具"""
    mcp_service = MCPService(db)
    success = mcp_service.enable_tool(tool_name)
    
    return {
        "success": success,
        "tool_name": tool_name,
        "action": "enabled"
    }

@router.post("/mcp/tools/{tool_name}/disable")
async def disable_mcp_tool(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """禁用 MCP 工具"""
    mcp_service = MCPService(db)
    success = mcp_service.disable_tool(tool_name)
    
    return {
        "success": success,
        "tool_name": tool_name,
        "action": "disabled"
    }

@router.post("/mcp/initialize")
async def initialize_default_tools(db: Session = Depends(get_db)):
    """初始化默认 MCP 工具"""
    mcp_service = MCPService(db)
    mcp_service.initialize_default_tools()
    
    return {
        "success": True,
        "message": "Default MCP tools initialized"
    }
