# services/tool_service.py
from core.user_vars import UserVars
from utils.parse_openapi import parse_openapi_tools
from utils.openapi_to_tools_json import openapi_to_mcp_tools
from core.tool_manager import ToolManager

class ToolService:
    def __init__(self):
        self.uv = UserVars()  # UserVars 可以作为实例属性复用

    def register_tools(self, user_id: int, openapi_json: dict, base_url: str):
        existing_tools = self.uv.get(user_id, "tools", {})
        existing_tools_info = self.uv.get(user_id, "tools_info", {})

        new_tools = parse_openapi_tools(openapi_json, base_url)
        new_tools_info = openapi_to_mcp_tools(openapi_json)

        existing_tools.update(new_tools)
        existing_tools_info.update(new_tools_info)

        self.uv.set(user_id, "tools", existing_tools)
        self.uv.set(user_id, "tools_info", existing_tools_info)

        return len(new_tools), len(existing_tools)

    def clear_tools(self, user_id: int):
        self.uv.set(user_id, "tools", {})
        self.uv.set(user_id, "tools_info", {})

    def test_tool(self, user_id: int, tool_id: str, params: dict):
        user_tools = self.uv.get(user_id, "tools", {})
        if not user_tools:
            raise ValueError("用户没有注册任何工具")

        tm = ToolManager(user_tools)
        return tm.call(tool_id, **params)

    def list_tools(self, user_id: int):
        user_tools = self.uv.get(user_id, "tools", {})
        result = []
        for name, info in user_tools.items():
            result.append({
                "name": name,
                "description": info.get("description"),
                "parameters": info.get("parameters", {})
            })
        return result
