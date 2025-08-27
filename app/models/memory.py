from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Memory(Base):
    __tablename__ = "memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)   # 外键关联 User
    thought = Column(String)
    action = Column(String)
    action_input = Column(String)               # JSON 格式
    observation = Column(String)
    summary = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
