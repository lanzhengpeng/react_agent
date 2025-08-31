from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str


class AgentRequest(BaseModel):
    task: str  # 用户任务描述

class AgentResponse(BaseModel):
    result: str  # 最终返回结果