from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from core.tool_manager import ToolManager
from models.user import User
from common.auth import get_current_user
from core.user_vars import UserVars
from utils.parse_openapi import parse_openapi_tools
from utils.openapi_to_tools_json import openapi_to_mcp_tools
router = APIRouter(prefix="/tool")  # ✅ 加上 tool 前缀

# ------------------ 数据模型 ------------------
class OpenAPIRegisterRequest(BaseModel):
    openapi_json: dict
    base_url: str

class ToolRegisterResponse(BaseModel):
    success: bool
    message: str

class ToolTestRequest(BaseModel):
    tool_id: str  # 工具唯一标识
    test_params: dict = {}  # 可选参数


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

        return ToolRegisterResponse(
            success=True,
            message=f"成功注册 {len(new_tools)} 个工具到用户 {current_user.username} 的内存，当前总工具数 {len(existing_tools)}"
        )
    except Exception as e:
        return ToolRegisterResponse(success=False, message=str(e))


# ------------------ 工具测试接口 ------------------
@router.post("/test")
def test_tool(request: ToolTestRequest, current_user: User = Depends(get_current_user)):
    """
    测试指定工具是否可用
    """
    uv = UserVars()
    user_id = current_user.id

    # 获取用户工具
    user_tools = uv.get(user_id, "tools", {})
    if not user_tools:
        raise HTTPException(status_code=404, detail="用户没有注册任何工具")

    tm = ToolManager(user_tools)  # ✅ 将用户工具传入 ToolManager

    try:
        # 调用工具
        result = tm.call(request.tool_id, **request.test_params)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
    

from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class ToolInfoResponse(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}  # 对应注册时的 parameters

class ToolListResponse(BaseModel):
    tools: List[ToolInfoResponse]


@router.get("/list", response_model=ToolListResponse)
def get_tools(current_user: User = Depends(get_current_user)):
    """
    获取当前用户注册的工具列表
    """
    uv = UserVars()
    user_id = current_user.id

    # 获取用户工具字典
    user_tools = uv.get(user_id, "tools", {})

    tool_list = []
    for name, info in user_tools.items():
        tool_list.append(
            ToolInfoResponse(
                name=name,
                description=info.get("description"),
                parameters=info.get("parameters", {})  # 保证是 dict
            )
        )

    return ToolListResponse(tools=tool_list)

