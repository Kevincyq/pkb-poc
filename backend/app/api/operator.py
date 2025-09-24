from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import OpsLog

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/commit")
def commit_op(item: dict, db: Session = Depends(get_db)):
    """
    PoC：落地一个操作日志（可扩展为生成 ICS 或调用日历 API）
    """
    op_type = item.get("op_type")
    payload = item.get("payload", {})
    log = OpsLog(op_type=op_type, payload=payload, status="committed", log="PoC commit ok")
    db.add(log); db.commit(); db.refresh(log)
    return {"status":"ok","op_id":str(log.id)}

