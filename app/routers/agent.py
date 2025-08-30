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
from core.user_vars import UserVars

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
        "username": current_user.username,
        "api_key":current_user.api_key,
        "model_url":current_user.model_url
    })

    return run_agent(request_dict)

# ------------------ 流式 Agent ------------------
@router.post("/run_agent_stream")
def run_agent_stream_endpoint(request: AgentRequest, current_user: User = Depends(get_current_user)):
    """
    流式运行 Agent 的 API 端点，返回 SSE 格式的流式响应
    """
    print("收到流式请求:", request.dict())

    def event_stream():
        # 先检查 api_key 和 model_url
        if not current_user.api_key or not current_user.model_url:
            error_event = {"status": "error", "message": "用户未提供 api_key 或 model_url"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            return

        # 构造字典传入 run_agent_stream
        request_dict = request.dict()
        request_dict.update({
            "user_id": current_user.id,
            "username": current_user.username,
            "api_key": current_user.api_key,
            "model_url": current_user.model_url,
            "model_name":current_user.model_name
        })

        for event in run_agent_stream(request_dict):
            if isinstance(event, dict):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            else:
                error_event = {"status": "error", "message": f"意外的事件格式: {type(event)}"}
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream; charset=utf-8")


# ------------------ 设置用户任务步骤提示词 ------------------
class TaskStepPromptRequest(BaseModel):
    task_step_prompt: str  # 用户自定义的任务步骤提示词

class TaskStepPromptResponse(BaseModel):
    success: bool
    message: str

@router.post("/set_task_step_prompt", response_model=TaskStepPromptResponse)
def set_task_step_prompt_endpoint(
    request: TaskStepPromptRequest,
    current_user: User = Depends(get_current_user)
):
    """
    设置当前用户的任务步骤提示词，后续 run_agent 或 run_agent_stream 会使用
    """
    try:
        uv = UserVars()
        uv.set(current_user.id, "task_step_prompt", request.task_step_prompt)
        return TaskStepPromptResponse(success=True, message="任务步骤提示词已保存")
    except Exception as e:
        return TaskStepPromptResponse(success=False, message=f"保存失败: {e}")




# ------------------ 工具注册接口 ------------------
@router.post("/register_tools", response_model=ToolRegisterResponse)
def register_tools(request: OpenAPIRegisterRequest, current_user: User = Depends(get_current_user)):
    """
    为当前用户注册工具，追加到已有工具中（同名工具会覆盖）
    """
    try:
        uv = UserVars()
        user_id = current_user.id

        # 获取用户已有的工具（如果没有就用空字典）
        existing_tools = uv.get(user_id, "tools", {})
        existing_tools_info = uv.get(user_id, "tools_info", {})

        # 解析请求中的工具
        new_tools = parse_openapi_tools(request.openapi_json, request.base_url)
        new_tools_info = openapi_to_mcp_tools(request.openapi_json)

        # 追加新工具到已有工具（同名覆盖）
        existing_tools.update(new_tools)
        existing_tools_info.update(new_tools_info)

        # 保存回 UserVars
        uv.set(user_id, "tools", existing_tools)
        uv.set(user_id, "tools_info", existing_tools_info)

        # 如果你还想在全局 registered_tools 做映射，可以用 user_id 作为前缀
        for name, info in new_tools.items():
            registered_tools[f"{user_id}_{name}"] = info

        return ToolRegisterResponse(
            success=True,
            message=f"成功注册 {len(new_tools)} 个工具到用户 {current_user.username} 的内存，当前总工具数 {len(existing_tools)}"
        )
    except Exception as e:
        return ToolRegisterResponse(success=False, message=str(e))
    

