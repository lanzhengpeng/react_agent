# controllers/tool_controller.py
from fastapi import APIRouter, Depends, HTTPException
from models.user_model import User
from core.auth import get_current_user
from services.tool_service import ToolService
from schemas.tool_schema import (
    OpenAPIRegisterRequest,
    ToolInfoResponse,
    ToolListResponse,
    ToolRegisterResponse,
    ToolTestRequest
)

router = APIRouter(prefix="/tool")

# 实例化 ToolService
tool_service = ToolService()

# ------------------ Controller ------------------
@router.post("/register_tools", response_model=ToolRegisterResponse)
def register_tools(request: OpenAPIRegisterRequest, current_user: User = Depends(get_current_user)):
    try:
        added_count, total_count = tool_service.register_tools(
            user_id=current_user.id,
            openapi_json=request.openapi_json,
            base_url=request.base_url
        )
        return ToolRegisterResponse(
            success=True,
            message=f"成功注册 {added_count} 个工具到用户 {current_user.username} 的内存，当前总工具数 {total_count}"
        )
    except Exception as e:
        return ToolRegisterResponse(success=False, message=str(e))

@router.delete("/clear_tools", response_model=ToolRegisterResponse)
def clear_tools(current_user: User = Depends(get_current_user)):
    try:
        tool_service.clear_tools(current_user.id)
        return ToolRegisterResponse(
            success=True,
            message=f"已清空用户 {current_user.username} 的所有工具"
        )
    except Exception as e:
        return ToolRegisterResponse(success=False, message=str(e))

@router.post("/test")
def test_tool(request: ToolTestRequest, current_user: User = Depends(get_current_user)):
    try:
        result = tool_service.test_tool(current_user.id, request.tool_id, request.test_params)
        return {"success": True, "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/list", response_model=ToolListResponse)
def get_tools(current_user: User = Depends(get_current_user)):
    tools = tool_service.list_tools(current_user.id)
    tool_list = [ToolInfoResponse(**t) for t in tools]
    return ToolListResponse(tools=tool_list)
