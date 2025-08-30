from sqlalchemy.orm import Session
from models.chat_session import ChatSession
from sqlalchemy.orm import Session
import json

def add_record(user_id: int, message_content: str, role: str, db: Session):
    """
    新增聊天记录
    :param user_id: 用户 ID
    :param message_content: 消息内容
    :param role: 消息角色，'user' 或 'assistant'
    :param db: 当前数据库会话
    :return: 返回保存的聊天记录对象
    """
    chat_session = ChatSession(
        user_id=user_id,
        message_content=message_content,
        role=role
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)  # 刷新获取数据库中的最新数据
    return chat_session


# 删除用户所有聊天记录的函数
def delete_all_records(user_id: int, db: Session):
    """
    删除指定用户的所有聊天记录
    :param user_id: 用户 ID
    :param db: 当前数据库会话
    :return: 返回删除的数量
    """
    deleted_count = db.query(ChatSession).filter(ChatSession.user_id == user_id).delete()
    db.commit()
    return deleted_count

def get_records_by_id(user_id: int, db: Session):
    """
    根据用户 ID 查询所有聊天记录并返回 JSON 格式数据
    :param user_id: 用户 ID
    :param db: 当前数据库会话
    :return: 返回聊天记录的 JSON 格式数据
    """
    chat_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    chat_sessions_data = [
        {
            "message_id": session.message_id,  # 使用 message_id 作为唯一标识
            "user_id": session.user_id,
            "message_content": session.message_content,
            "role": session.role.value,  # 将 Role 枚举转换为其值
            "created_at": session.created_at.isoformat()  # 转换为 ISO 格式字符串
        }
        for session in chat_sessions
    ]
    return json.dumps(chat_sessions_data, ensure_ascii=False, indent=4)