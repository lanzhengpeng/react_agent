# services/tool_service.py
from core.user_vars import UserVars
from utils.parse_openapi import parse_openapi_tools
from utils.openapi_to_tools_json import openapi_to_mcp_tools
from core.tool_manager import ToolManager
from sqlalchemy.orm import Session
from models.tool_model import Tool
import httpx
import json

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

        # ---------- 工具信息（list，按 name 覆盖/追加） ----------
        tools_dict = {tool["name"]: tool for tool in existing_tools_info.get("tools", [])}
        for tool in new_tools_info.get("tools", []):
            tools_dict[tool["name"]] = tool
        existing_tools_info["tools"] = list(tools_dict.values())

        # ---------- 存回去 ----------
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
        从数据库加载该用户所有工具到 UserVars，同时与内存已有工具合并（同名覆盖）
        返回加载的工具数量
        """
        tools = self.db.query(Tool).filter_by(user_id=user_id).all()

        def make_func(url, method):
            def func(**kwargs):
                if method.lower() == "get":
                    r = httpx.get(url, params=kwargs)
                else:
                    r = httpx.post(url, json=kwargs)
                r.raise_for_status()
                try:
                    return r.json()
                except Exception:
                    return r.text
            return func

        # 从数据库生成工具 dict 和 list
        db_tools_dict = {}
        db_tools_info = {}
        for t in tools:
            schema = t.input_schema
            if isinstance(schema, str):
                try:
                    schema = json.loads(schema)
                except Exception:
                    schema = {}
            db_tools_dict[t.name] = {
                "func": make_func(t.url, t.method),
                "description": t.description,
                "url": t.url,
                "method": t.method,
                "parameters": schema
            }
            db_tools_info[t.name] = {
                "name": t.name,
                "description": t.description,
                "url": t.url,
                "method": t.method,
                "input_schema": schema
            }

        # -------- merge 到内存已有工具 --------
        existing_tools = self.uv.get(user_id, "tools", {})
        existing_tools_info = self.uv.get(user_id, "tools_info", {"tools": []})

        # 工具本身（dict，按 name 覆盖/追加）
        existing_tools.update(db_tools_dict)

        # 工具信息（list，转 dict 按 name 覆盖，再转回 list）
        tools_info_map = {tool["name"]: tool for tool in existing_tools_info.get("tools", [])}
        tools_info_map.update(db_tools_info)
        tools_info_list = list(tools_info_map.values())

        # 存回去
        self.uv.set(user_id, "tools", existing_tools)
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