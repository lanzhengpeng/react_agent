# app/models/user.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from datetime import datetime
Base = declarative_base()
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    api_key = Column(String(128), unique=True, nullable=True)
    model_url = Column(String(256), nullable=True)  # 用户大模型服务地址
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="active")  # 可选：active / disabled
