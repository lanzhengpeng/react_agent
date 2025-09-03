from pydantic import BaseModel
from typing import Dict, Any, List, Optional
# ------------------ 数据模型 ------------------
class OpenAPIRegisterRequest(BaseModel):
    openapi_json: dict
    base_url: str

class ToolRegisterResponse(BaseModel):
    success: bool
    message: str

class ToolTestRequest(BaseModel):
    tool_id: str
    test_params: Dict[str, Any] = {}

class ToolInfoResponse(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}


class ToolListResponse(BaseModel):
    tools: List[ToolInfoResponse]


class SaveToolRequest(BaseModel):
    tool_name: str


class DeleteToolRequest(BaseModel):
    tool_name: str
