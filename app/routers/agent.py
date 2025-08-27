from fastapi import APIRouter
# from models.request import AgentRequest
# from models.response import AgentResponse
from core.agent import run_agent
from pydantic import BaseModel
from typing import Dict
from utils.parse_openapi import parse_openapi_tools  # 直接导入你的解析函数
from utils.openapi_to_tools_json import openapi_to_mcp_tools
from core.global_vars import GlobalVars
import json

# 获取全局管理器实例
gv = GlobalVars()

# 初始化全局变量
gv.set("tools", {})
gv.set("tools_info",{})


router = APIRouter()

# 内存存储工具（可换成DB）
registered_tools: Dict[str, dict] = {}

class OpenAPIRegisterRequest(BaseModel):
    openapi_json: dict
    base_url: str

class ToolRegisterResponse(BaseModel):
    success: bool
    message: str

# ------------------ 模型定义 ------------------
class AgentRequest(BaseModel):
    task: str  # 用户任务描述

class AgentResponse(BaseModel):
    result: str  # 最终返回结果
@router.post("/run_agent")
def run_agent_endpoint(request: AgentRequest):
    # 打印调试信息
    print("收到请求:", request.dict())
    
    # 将 Pydantic 对象转换为字典传入 run_agent
    return run_agent(request.dict())

from fastapi.responses import StreamingResponse
from core.agent import run_agent_stream  # 这是我们改造过的流式版本

from fastapi.responses import StreamingResponse

@router.post("/run_agent_stream")
def run_agent_stream_endpoint(request: AgentRequest):
    print("收到流式请求:", request.dict())

    def event_stream():
        for event in run_agent_stream(request.dict()):
            # 如果 event 是列表或者字符数组，先拼成完整字符串
            if isinstance(event, list):
                event = "".join(event)
            # 直接 yield 字符串，不再用 json.dumps
            yield event

    return StreamingResponse(event_stream(), media_type="text/plain; charset=utf-8")



# 新的批量注册接口
@router.post("/register_tools", response_model=ToolRegisterResponse)
def register_tools(request: OpenAPIRegisterRequest):
    try:
        gv.set("tools", parse_openapi_tools(request.openapi_json, request.base_url))
        gv.set("tools_info",openapi_to_mcp_tools(request.openapi_json))
        for name, info in gv.get("tools").items():
            registered_tools[name] = info

        return ToolRegisterResponse(
            success=True,
            message = f"成功注册 {len(gv.get('tools'))} 个工具到内存"

        )
    except Exception as e:
        return ToolRegisterResponse(success=False, message=str(e))
