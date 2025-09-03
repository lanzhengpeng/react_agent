# models/task_prompt_model.py
from sqlalchemy import Column, Integer, Text, ForeignKey
from core.database import Base

class TaskPrompt(Base):
    __tablename__ = "task_prompts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
