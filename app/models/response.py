from pydantic import BaseModel

class AgentResponse(BaseModel):
    result: str
