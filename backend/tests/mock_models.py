"""
Mock模型模块，避免pgvector依赖
在测试中替代app.models
"""
import sys
from unittest.mock import MagicMock

# Mock pgvector模块
sys.modules['pgvector'] = MagicMock()
sys.modules['pgvector.sqlalchemy'] = MagicMock()

# 现在可以安全导入原始模型
from app.models import *
