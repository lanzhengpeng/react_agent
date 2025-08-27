from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from fastapi.responses import StreamingResponse
import json

from core.agent import run_agent, run_agent_stream
from utils.parse_openapi import parse_openapi_tools
from utils.openapi_to_tools_json import openapi_to_mcp_tools
from core.global_vars import GlobalVars
from common.auth import get_current_user
from models.user import User

# 获取全局管理器实例
gv = GlobalVars()
gv.set("tools", {})
gv.set("tools_info", {})

router = APIRouter(prefix="/agent", tags=["agent"])
# 内存存储工具（可换成DB）
registered_tools: Dict[str, dict] = {}

# ------------------ 请求/响应模型 ------------------
class OpenAPIRegisterRequest(BaseModel):
    openapi_json: dict
    base_url: str

class ToolRegisterResponse(BaseModel):
    success: bool
    message: str

class AgentRequest(BaseModel):
    task: str  # 用户任务描述

class AgentResponse(BaseModel):
    result: str  # 最终返回结果

# ------------------ 非流式 Agent ------------------
@router.post("/run_agent")
def run_agent_endpoint(request: AgentRequest, current_user: User = Depends(get_current_user)):
    """
    普通调用 Agent 接口，返回最终结果
    """
    # 打印调试信息
    print("收到请求:", request.dict())

    # 构造字典传入 run_agent
    request_dict = request.dict()
    request_dict.update({
        "user_id": current_user.id,
        "username": current_user.username
    })

    return run_agent(request_dict)

# ------------------ 流式 Agent ------------------
@router.post("/run_agent_stream")
def run_agent_stream_endpoint(request: AgentRequest, current_user: User = Depends(get_current_user)):
    """
    流式运行 Agent 的 API 端点，返回 SSE 格式的流式响应
    """
    print("收到流式请求:", request.dict())

    # 构造字典传入 run_agent_stream
    request_dict = request.dict()
    request_dict.update({
        "user_id": current_user.id,
        "username": current_user.username
    })

    def event_stream():
        for event in run_agent_stream(request_dict):
            if isinstance(event, dict):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            else:
                error_event = {"status": "error", "message": f"意外的事件格式: {type(event)}"}
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream; charset=utf-8")

# ------------------ 工具注册接口 ------------------
@router.post("/register_tools", response_model=ToolRegisterResponse)
def register_tools(request: OpenAPIRegisterRequest):
    try:
        gv.set("tools", parse_openapi_tools(request.openapi_json, request.base_url))
        gv.set("tools_info", openapi_to_mcp_tools(request.openapi_json))
        for name, info in gv.get("tools").items():
            registered_tools[name] = info

        return ToolRegisterResponse(
            success=True,
            message=f"成功注册 {len(gv.get('tools'))} 个工具到内存"
        )
    except Exception as e:
        return ToolRegisterResponse(success=False, message=str(e))
