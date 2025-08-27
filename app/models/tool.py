from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # 外键关联 User
    tool_name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)   # 工具的 OpenAPI URL
    tool_config = Column(String)                # JSON 配置，可选
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
