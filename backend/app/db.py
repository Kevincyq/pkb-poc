import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
Base = declarative_base()

# 只有在有DATABASE_URL时才创建引擎
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # 测试环境或未配置数据库时的占位符
    engine = None
    SessionLocal = None


def get_db():
    """获取数据库会话"""
    if SessionLocal is None:
        raise RuntimeError("Database not configured. Please set DATABASE_URL environment variable.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



