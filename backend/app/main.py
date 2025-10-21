from fastapi import FastAPI, Request
from app.api import ingest, search, operator, qa, agent, document, embedding, category, collection, files, files_improved, auth
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.db import engine, Base
from app.models import Content, Chunk, QAHistory, AgentTask, MCPTool, OpsLog, Category, ContentCategory, Collection, User, CloudAuth, StorageConfig
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import os

# 🔥 配置Debug日志级别
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 设置特定模块的日志级别
logging.getLogger("app.api.files").setLevel(logging.DEBUG)
logging.getLogger("app.api.ingest").setLevel(logging.DEBUG)
logging.getLogger("app.workers.tasks").setLevel(logging.DEBUG)
logging.getLogger("app.workers.quick_tasks").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info(f"🚀 PKB Backend starting with log level: {log_level}")

# 创建数据库表结构
Base.metadata.create_all(bind=engine)

# 自动初始化系统分类
def initialize_system_data():
    """应用启动时自动初始化系统数据"""
    try:
        from app.db import SessionLocal
        from app.services.category_service import CategoryService
        
        db = SessionLocal()
        try:
            category_service = CategoryService(db)
            success = category_service.initialize_system_categories()
            if success:
                logger.info("✅ System categories initialized successfully")
            else:
                logger.warning("⚠️ Failed to initialize system categories")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error during system initialization: {e}")

# 执行系统初始化
initialize_system_data()

# 初始化默认用户
def initialize_default_user():
    """初始化默认用户"""
    try:
        from app.scripts.init_default_user import create_default_user, migrate_existing_content
        create_default_user()
        migrate_existing_content()
        logger.info("✅ Default user initialization completed")
    except Exception as e:
        logger.error(f"❌ Error during default user initialization: {e}")

# 执行默认用户初始化
initialize_default_user()

class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """处理代理头的中间件，确保FastAPI正确识别HTTPS协议"""
    async def dispatch(self, request: Request, call_next):
        # 检查代理头，修正协议信息
        if "x-forwarded-proto" in request.headers:
            forwarded_proto = request.headers["x-forwarded-proto"]
            if forwarded_proto == "https":
                # 确保FastAPI知道这是HTTPS请求
                request.scope["scheme"] = "https"
        
        # 处理X-Forwarded-Ssl头
        if "x-forwarded-ssl" in request.headers and request.headers["x-forwarded-ssl"] == "on":
            request.scope["scheme"] = "https"
            
        response = await call_next(request)
        return response

app = FastAPI(
        title="PKB-backend",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None
        )

# 添加代理头处理中间件（必须在CORS之前）
app.add_middleware(ProxyHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pkb.kmchat.cloud",
        "https://pkb-test.kmchat.cloud", 
        "https://kb.kmchat.cloud",
        "https://nextcloud.kmchat.cloud",
        "https://pkb-poc.kmchat.cloud",
        "https://pkb-frontend.vercel.app",
        "https://test-pkb.kmchat.cloud",
        # Vercel预览和生产域名
        "https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app",
        "https://pkb-poc-kevincyqs-projects.vercel.app",
        "https://pkb-poc.vercel.app",
        # 允许所有Vercel子域名（开发时使用）
        "*"
    ],
    allow_credentials=False,  # 改为False，避免CORS问题
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.include_router(ingest.router,   prefix="/api/ingest",   tags=["ingest"])
app.include_router(search.router,   prefix="/api/search",   tags=["search"])
app.include_router(qa.router,       prefix="/api/qa",       tags=["qa"])
app.include_router(agent.router,    prefix="/api/agent",    tags=["agent"])
app.include_router(document.router, prefix="/api/document", tags=["document"])
app.include_router(embedding.router, prefix="/api/embedding", tags=["embedding"])
app.include_router(category.router, prefix="/api/category", tags=["category"])
app.include_router(collection.router, prefix="/api/collection", tags=["collection"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(files_improved.router, prefix="/api/files_improved", tags=["files_improved"])
app.include_router(operator.router, prefix="/api/operator", tags=["operator"])
app.include_router(auth.router, prefix="/api", tags=["auth"])

@app.get("/", include_in_schema=False)
def root():
    response = RedirectResponse(url="/api/docs")
    # 为重定向响应添加 CORS 头
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.get("/api/health")
def health():
    return {"status": "ok"}

