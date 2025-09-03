# services/tool_service.py
from core.user_vars import UserVars
from utils.parse_openapi import parse_openapi_tools
from utils.openapi_to_tools_json import openapi_to_mcp_tools
from core.tool_manager import ToolManager
from sqlalchemy.orm import Session
from models.tool_model import Tool
import httpx


class ToolService:

    def __init__(self, db: Session):
        self.uv = UserVars()  # UserVars 可以作为实例属性复用
        self.db = db

    def register_tools(self, user_id: int, openapi_json: dict, base_url: str):
        existing_tools = self.uv.get(user_id, "tools", {})
        existing_tools_info = self.uv.get(user_id, "tools_info", {"tools": []})

        new_tools = parse_openapi_tools(openapi_json, base_url)
        new_tools_info = openapi_to_mcp_tools(openapi_json)  # {"tools": [...]}

        # 工具本身可以直接 dict update（按 name 覆盖/追加）
        existing_tools.update(new_tools)

        # 工具信息是 list，改为追加
        if "tools" not in existing_tools_info:
            existing_tools_info["tools"] = []
        existing_tools_info["tools"].extend(new_tools_info.get("tools", []))

        # 存回去
        self.uv.set(user_id, "tools", existing_tools)
        self.uv.set(user_id, "tools_info", existing_tools_info)

        return len(new_tools), len(existing_tools_info.get("tools", []))

    def clear_tools(self, user_id: int):
        self.uv.set(user_id, "tools", {})
        self.uv.set(user_id, "tools_info", {"tools": []})

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

        # ===== 按名字存入数据库 =====
    def save_tool_to_db(self, user_id: int, tool_name: str):
        """
        将指定工具按名字存入数据库，如果存在同名则覆盖
        """
        user_tools = self.uv.get(user_id, "tools", {})
        if tool_name not in user_tools:
            raise ValueError(f"工具 {tool_name} 不存在于 UserVars")

        tool_info = user_tools[tool_name]

        tool_obj = self.db.query(Tool).filter_by(user_id=user_id,
                                                 name=tool_name).first()
        if not tool_obj:
            tool_obj = Tool(user_id=user_id, name=tool_name)

        tool_obj.description = tool_info.get("description")
        tool_obj.url = tool_info.get("url")  # 注意这里改成 url
        tool_obj.method = tool_info.get("method")
        tool_obj.input_schema = tool_info.get("parameters")

        self.db.add(tool_obj)
        self.db.commit()
        return True

    # ===== 从数据库加载全部工具到 UserVars =====
    def load_tools_from_db(self, user_id: int):
        """
        从数据库加载该用户所有工具到 UserVars，同时生成可调用函数
        返回加载的工具数量
        """
        tools = self.db.query(Tool).filter_by(user_id=user_id).all()

        tools_dict = {}
        tools_info_list = []

        def make_func(url, method):
            """
            生成可调用函数，url 已经是完整路径
            """

            def func(**kwargs):
                if method.lower() == "get":
                    r = httpx.get(url, params=kwargs)
                else:
                    r = httpx.post(url, json=kwargs)
                r.raise_for_status()
                try:
                    return r.json()
                except:
                    return r.text

            return func

        for t in tools:
            tools_dict[t.name] = {
                "func": make_func(t.url, t.method),  # 生成可调用函数
                "description": t.description,
                "url": t.url,
                "method": t.method,
                "parameters": t.input_schema
            }
            tools_info_list.append({
                "name": t.name,
                "description": t.description,
                "url": t.url,
                "method": t.method,
                "input_schema": t.input_schema
            })

        self.uv.set(user_id, "tools", tools_dict)
        self.uv.set(user_id, "tools_info", {"tools": tools_info_list})

        return len(tools)
    # ===== 根据名字删除数据库里的工具 =====
    def delete_tool_from_db(self, user_id: int, tool_name: str):
        """
        根据工具名字删除数据库中的工具
        """
        tool_obj = self.db.query(Tool).filter_by(user_id=user_id, name=tool_name).first()
        if not tool_obj:
            raise ValueError(f"工具 {tool_name} 不存在于数据库")

        self.db.delete(tool_obj)
        self.db.commit()
        return True