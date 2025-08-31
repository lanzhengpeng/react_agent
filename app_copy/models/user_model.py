from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

# 用户状态的枚举类
class UserStatus(PyEnum):
    active = "active"
    disabled = "disabled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    api_key = Column(String(128), unique=True, nullable=True)
    model_url = Column(String(256), nullable=True)  # 用户大模型服务地址
    model_name = Column(String, nullable=True)  # 新增字段：大模型的名称
    created_at = Column(DateTime, default=datetime.now)
    status = Column(Enum(UserStatus), default=UserStatus.active)  # 改进：使用枚举类型限定状态值

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, status={self.status})>"
