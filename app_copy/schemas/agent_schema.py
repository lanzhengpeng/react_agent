from pydantic import BaseModel
from typing import Optional
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str


class AgentRequest(BaseModel):
    task: str  # 用户任务描述


class AgentResponse(BaseModel):
    result: str  # 最终返回结果

class TaskStepPromptRequest(BaseModel):
    task_step_prompt: str  # 用户自定义的任务步骤提示词

class TaskStepPromptResponse(BaseModel):
    success: bool
    message: str
    prompt: Optional[str] = None   # ✅ 新增字段

