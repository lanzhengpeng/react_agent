from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from common.database import get_db  # 假设你有一个 get_db 函数获取数据库会话
from core.chat_session import delete_all_records,get_records_by_id
from common.auth import get_current_user  # 引入 get_current_user 来获取当前用户
from models.user import User
router = APIRouter(prefix="/chat_session", tags=["chat_session"])

@router.delete("/clear_chat_history")
async def clear_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    清除当前用户的聊天记录的接口
    :param current_user: 当前登录的用户
    :param db: 数据库会话
    :return: 返回删除成功的信息
    """
    try:
        # 使用 current_user.id 来清除当前用户的聊天记录
        delete_all_records( current_user.id,db)
        return {"message": "聊天记录已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_chat_history")
async def get_chat_history(current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """
    获取当前用户的所有聊天记录的接口
    :param current_user: 当前登录的用户
    :param db: 数据库会话
    :return: 返回用户的所有聊天记录
    """
    print("12213")
    try:
        # 使用 current_user.id 获取当前用户的聊天记录
        chat_sessions = get_records_by_id(current_user.id, db)
        if not chat_sessions:
            raise HTTPException(status_code=404, detail="没有找到聊天记录")

        return {"chat_sessions": chat_sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
