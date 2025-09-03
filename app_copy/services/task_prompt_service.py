# services/task_prompt_service.py
from sqlalchemy.orm import Session
from models.task_prompt_model import TaskPrompt
from services.agent_service import Agent

class TaskPromptService:

    def __init__(self, db: Session):
        self.db = db

    def save_prompt(self, user_id: int, prompt: str):
        # 如果用户已有提示词，就更新；否则插入
        obj = self.db.query(TaskPrompt).filter_by(user_id=user_id).first()
        if obj:
            obj.prompt = prompt
        else:
            obj = TaskPrompt(user_id=user_id, prompt=prompt)
            self.db.add(obj)
        self.db.commit()
        return True
    def load_task_step_prompt(self, user_id: int):
        """
        从数据库加载提示词到内存
        """
        prompt = self.db.query(TaskPrompt).filter(TaskPrompt.user_id == user_id).first()
        if not prompt or not prompt.prompt:
            raise ValueError("数据库中没有保存的提示词")

        agent = Agent(user_id=user_id, db=self.db)
        agent.set_task_step_prompt(prompt.prompt)  # ✅ 复用 set_task_step_prompt
        return True