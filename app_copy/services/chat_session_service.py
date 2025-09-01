from sqlalchemy.orm import Session
from models.chat_session_model import ChatSession
import json


class ChatSessionService:
    """聊天记录服务类"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def add_record(self, message_content: str, role: str):
        """
        新增聊天记录
        """
        chat_session = ChatSession(
            user_id=self.user_id,
            message_content=message_content,
            role=role
        )
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        return chat_session

    def delete_all_records(self):
        """
        删除当前用户的所有聊天记录
        """
        deleted_count = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == self.user_id)
            .delete()
        )
        self.db.commit()
        return deleted_count

    def get_records(self):
        """
        获取当前用户的所有聊天记录（返回列表字典）
        """
        chat_sessions = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == self.user_id)
            .all()
        )
        chat_sessions_data = [
            {
                "message_id": session.message_id,
                "user_id": session.user_id,
                "message_content": session.message_content,
                "role": session.role.value,  # 枚举转值
                "created_at": session.created_at.isoformat()
            }
            for session in chat_sessions
        ]
        return chat_sessions_data  # ✅ 返回对象，不用 json.dumps

    
    # 新增方法
    def format_history(self, user_task: str, separator: str = "\n-------\n用户任务:\n") -> str:
        """
        将用户聊天历史格式化为带角色标签、多轮分隔符的字符串，拼接当前任务
        如果没有历史记录，会提示“暂无聊天记录”
        """
        chat_history = self.get_records()
        formatted_messages = []

        if not chat_history:
            formatted_messages.append("暂无聊天记录")
        else:
            for msg in chat_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg.get("message_content", "")
                formatted_messages.append(f"[{role}]: {content}")

        return "\n".join(formatted_messages) + separator + f"[User Task]: {user_task}"

