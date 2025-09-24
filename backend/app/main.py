from fastapi import FastAPI
from app.api import ingest, search, operator, qa, agent, document, embedding, category, collection, files
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.db import engine, Base
from app.models import Content, Chunk, QAHistory, AgentTask, MCPTool, OpsLog, Category, ContentCategory, Collection

# 创建数据库表结构
Base.metadata.create_all(bind=engine)

app = FastAPI(
        title="PKB-backend",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pkb.kmchat.cloud",
        "https://kb.kmchat.cloud",
        "https://nextcloud.kmchat.cloud",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(operator.router, prefix="/api/operator", tags=["operator"])

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/api/docs")


@app.get("/api/health")
def health():
    return {"status": "ok"}
