from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from core.database import get_db
from core.auth import get_current_user
from models.user_model import User
from services.chat_session_service import ChatSessionService

router = APIRouter(prefix="/chat_session", tags=["chat_session"])

# ------------------ 获取聊天记录 ----------------
@router.get("/get_chat_history", response_model=List[Dict])
def get_chat_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的所有聊天记录
    """
    service = ChatSessionService(user_id=current_user.id, db=db)
    records = service.get_records()
    return records


# ------------------ 删除聊天记录 ----------------
@router.delete("/clear_chat_history")
def delete_chat_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除当前用户的所有聊天记录
    """
    service = ChatSessionService(user_id=current_user.id, db=db)
    deleted_count = service.delete_all_records()
    return {"message": f"已删除 {deleted_count} 条聊天记录"}
