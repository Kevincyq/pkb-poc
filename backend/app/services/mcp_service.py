"""
MCP (Model Context Protocol) 服务
支持工具注册、调用和管理
"""
import json
import requests
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models import MCPTool
import logging

logger = logging.getLogger(__name__)

class MCPService:
    def __init__(self, db: Session):
        self.db = db
        self.registered_tools = {}
        self._load_tools()
    
    def _load_tools(self):
        """加载已注册的工具"""
        try:
            tools = self.db.query(MCPTool).filter(MCPTool.enabled == True).all()
            for tool in tools:
                self.registered_tools[tool.name] = {
                    "id": str(tool.id),
                    "description": tool.description,
                    "category": tool.category,
                    "config": tool.config
                }
            logger.info(f"Loaded {len(self.registered_tools)} MCP tools")
        except Exception as e:
            logger.error(f"Error loading MCP tools: {e}")
    
    def register_tool(
        self, 
        name: str, 
        description: str, 
        category: str, 
        config: Dict
    ) -> bool:
        """
        注册新的 MCP 工具
        
        Args:
            name: 工具名称
            description: 工具描述
            category: 工具类别 (connector, executor, reader, writer)
            config: 工具配置
        
        Returns:
            注册是否成功
        """
        try:
            # 检查工具是否已存在
            existing_tool = self.db.query(MCPTool).filter(MCPTool.name == name).first()
            if existing_tool:
                logger.warning(f"Tool {name} already exists")
                return False
            
            # 创建新工具
            tool = MCPTool(
                name=name,
                description=description,
                category=category,
                config=config
            )
            
            self.db.add(tool)
            self.db.commit()
            self.db.refresh(tool)
            
            # 更新内存中的工具列表
            self.registered_tools[name] = {
                "id": str(tool.id),
                "description": description,
                "category": category,
                "config": config
            }
            
            logger.info(f"Successfully registered MCP tool: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering MCP tool {name}: {e}")
            self.db.rollback()
            return False
    
    def call_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            parameters: 调用参数
        
        Returns:
            工具执行结果
        """
        if tool_name not in self.registered_tools:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found"
            }
        
        tool_config = self.registered_tools[tool_name]
        
        try:
            # 根据工具类别调用不同的处理方法
            if tool_config["category"] == "connector":
                return self._call_connector_tool(tool_name, tool_config, parameters)
            elif tool_config["category"] == "executor":
                return self._call_executor_tool(tool_name, tool_config, parameters)
            elif tool_config["category"] == "reader":
                return self._call_reader_tool(tool_name, tool_config, parameters)
            elif tool_config["category"] == "writer":
                return self._call_writer_tool(tool_name, tool_config, parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool category: {tool_config['category']}"
                }
                
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _call_connector_tool(self, tool_name: str, tool_config: Dict, parameters: Dict) -> Dict:
        """调用连接器类工具"""
        config = tool_config["config"]
        
        if tool_name == "map_connector":
            return self._call_map_service(parameters)
        elif tool_name == "wallet_connector":
            return self._call_wallet_service(parameters)
        elif tool_name == "health_connector":
            return self._call_health_service(parameters)
        else:
            return self._call_generic_api(config, parameters)
    
    def _call_executor_tool(self, tool_name: str, tool_config: Dict, parameters: Dict) -> Dict:
        """调用执行器类工具"""
        config = tool_config["config"]
        
        if tool_name == "email_executor":
            return self._execute_email_action(parameters)
        elif tool_name == "document_executor":
            return self._execute_document_action(parameters)
        elif tool_name == "navigation_executor":
            return self._execute_navigation_action(parameters)
        else:
            return self._execute_generic_action(config, parameters)
    
    def _call_reader_tool(self, tool_name: str, tool_config: Dict, parameters: Dict) -> Dict:
        """调用读取器类工具"""
        # TODO: 实现读取器工具逻辑
        return {
            "success": False,
            "error": "Reader tools not implemented yet"
        }
    
    def _call_writer_tool(self, tool_name: str, tool_config: Dict, parameters: Dict) -> Dict:
        """调用写入器类工具"""
        # TODO: 实现写入器工具逻辑
        return {
            "success": False,
            "error": "Writer tools not implemented yet"
        }
    
    def _call_map_service(self, parameters: Dict) -> Dict:
        """调用地图服务"""
        # TODO: 集成地图 API
        return {
            "success": False,
            "error": "Map service not implemented yet",
            "data": parameters
        }
    
    def _call_wallet_service(self, parameters: Dict) -> Dict:
        """调用钱包服务"""
        # TODO: 集成钱包 API
        return {
            "success": False,
            "error": "Wallet service not implemented yet",
            "data": parameters
        }
    
    def _call_health_service(self, parameters: Dict) -> Dict:
        """调用健康服务"""
        # TODO: 集成健康数据 API
        return {
            "success": False,
            "error": "Health service not implemented yet",
            "data": parameters
        }
    
    def _execute_email_action(self, parameters: Dict) -> Dict:
        """执行邮件操作"""
        action = parameters.get("action", "send")
        
        if action == "send":
            # TODO: 发送邮件
            return {
                "success": False,
                "error": "Email sending not implemented yet"
            }
        elif action == "read":
            # TODO: 读取邮件
            return {
                "success": False,
                "error": "Email reading not implemented yet"
            }
        else:
            return {
                "success": False,
                "error": f"Unknown email action: {action}"
            }
    
    def _execute_document_action(self, parameters: Dict) -> Dict:
        """执行文档操作"""
        action = parameters.get("action", "create")
        
        if action == "create":
            # TODO: 创建文档
            return {
                "success": False,
                "error": "Document creation not implemented yet"
            }
        elif action == "edit":
            # TODO: 编辑文档
            return {
                "success": False,
                "error": "Document editing not implemented yet"
            }
        else:
            return {
                "success": False,
                "error": f"Unknown document action: {action}"
            }
    
    def _execute_navigation_action(self, parameters: Dict) -> Dict:
        """执行导航操作"""
        # TODO: 集成导航服务
        return {
            "success": False,
            "error": "Navigation service not implemented yet"
        }
    
    def _call_generic_api(self, config: Dict, parameters: Dict) -> Dict:
        """调用通用 API"""
        try:
            url = config.get("url")
            method = config.get("method", "POST")
            headers = config.get("headers", {})
            
            if not url:
                return {
                    "success": False,
                    "error": "No URL configured for tool"
                }
            
            response = requests.request(
                method=method,
                url=url,
                json=parameters,
                headers=headers,
                timeout=30
            )
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": response.json() if response.content else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_generic_action(self, config: Dict, parameters: Dict) -> Dict:
        """执行通用操作"""
        # 类似于 _call_generic_api，但用于执行器类工具
        return self._call_generic_api(config, parameters)
    
    def get_available_tools(self) -> Dict[str, Dict]:
        """获取可用工具列表"""
        return self.registered_tools
    
    def get_tools_by_category(self, category: str) -> Dict[str, Dict]:
        """按类别获取工具"""
        return {
            name: tool_info 
            for name, tool_info in self.registered_tools.items() 
            if tool_info["category"] == category
        }
    
    def enable_tool(self, tool_name: str) -> bool:
        """启用工具"""
        try:
            tool = self.db.query(MCPTool).filter(MCPTool.name == tool_name).first()
            if tool:
                tool.enabled = True
                self.db.commit()
                self._load_tools()  # 重新加载
                return True
            return False
        except Exception as e:
            logger.error(f"Error enabling tool {tool_name}: {e}")
            return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """禁用工具"""
        try:
            tool = self.db.query(MCPTool).filter(MCPTool.name == tool_name).first()
            if tool:
                tool.enabled = False
                self.db.commit()
                if tool_name in self.registered_tools:
                    del self.registered_tools[tool_name]
                return True
            return False
        except Exception as e:
            logger.error(f"Error disabling tool {tool_name}: {e}")
            return False
    
    def update_tool_config(self, tool_name: str, new_config: Dict) -> bool:
        """更新工具配置"""
        try:
            tool = self.db.query(MCPTool).filter(MCPTool.name == tool_name).first()
            if tool:
                tool.config = new_config
                self.db.commit()
                self._load_tools()  # 重新加载
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating tool config {tool_name}: {e}")
            return False
    
    def initialize_default_tools(self):
        """初始化默认工具"""
        default_tools = [
            {
                "name": "map_connector",
                "description": "连接地图服务，获取位置信息和导航",
                "category": "connector",
                "config": {
                    "api_key": "",
                    "service": "google_maps"
                }
            },
            {
                "name": "wallet_connector", 
                "description": "连接钱包服务，查询余额和交易",
                "category": "connector",
                "config": {
                    "wallet_type": "digital",
                    "api_endpoint": ""
                }
            },
            {
                "name": "health_connector",
                "description": "连接健康数据服务",
                "category": "connector", 
                "config": {
                    "data_source": "apple_health",
                    "api_key": ""
                }
            },
            {
                "name": "email_executor",
                "description": "执行邮件相关操作",
                "category": "executor",
                "config": {
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": ""
                }
            },
            {
                "name": "document_executor",
                "description": "执行文档操作",
                "category": "executor",
                "config": {
                    "storage_type": "nextcloud",
                    "api_endpoint": ""
                }
            }
        ]
        
        for tool_config in default_tools:
            self.register_tool(
                name=tool_config["name"],
                description=tool_config["description"],
                category=tool_config["category"],
                config=tool_config["config"]
            )
