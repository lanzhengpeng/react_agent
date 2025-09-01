from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class RegisterRequest(BaseModel):
    username: str
    password: str
    api_key: Optional[str] = None
    model_url: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateModelRequest(BaseModel):
    api_key: str
    model_url: str
    model_name: str
