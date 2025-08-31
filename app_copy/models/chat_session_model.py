# app/models/chat_session.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

# 角色枚举类
class Role(PyEnum):
    user = "user"
    assistant = "assistant"
    system = "system"

class ChatSession(Base):
    __tablename__ = "chat_session"  # 确保表名正确

    message_id = Column(Integer, primary_key=True, index=True)  # 修改为 message_id
    user_id = Column(Integer, nullable=False)  # 没有外键约束  
    role = Column(Enum(Role), nullable=False)  # 角色（用户、助手或系统）
    message_content = Column(String, nullable=False)  # 消息内容
    created_at = Column(DateTime, default=datetime.now)  # 创建时间，默认为当前时间


    def __repr__(self):
        return f"<ChatSession(message_id={self.message_id}, users_id={self.user_id}, role={self.role}, created_at={self.created_at})>"
