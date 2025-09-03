# schemas/task_prompt_schema.py
from pydantic import BaseModel

class SavePromptRequest(BaseModel):
    prompt: str

class SavePromptResponse(BaseModel):
    success: bool
    message: str
