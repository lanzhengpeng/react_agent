from sqlalchemy import Column, Integer, String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)       # 标识属于哪个用户
    name = Column(String(255), nullable=False)     # 工具名
    description = Column(Text)                     # 工具描述
    url = Column(String(255), nullable=False)     # 完整请求 URL
    method = Column(String(10), nullable=False)   # 请求方法
    input_schema = Column(JSON)                    # 输入参数的完整 schema

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_tool_name"),  # 同一用户下工具名唯一
    )
