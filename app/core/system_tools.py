# app/tools/history_tools.py
from typing import Callable, Dict
from core.memory import Memory



def get_history_by_round_tool(memory: Memory) -> Callable[[int], Dict]:
    """
    返回指定轮数的完整历史信息工具函数
    """
    def func(round: int) -> Dict:
        full_history = memory.get_full_history()
        idx = round - 1
        if 0 <= idx < len(full_history):
            return full_history[idx]
        return {}
    return func


def register_history_tools(memory: Memory) -> Dict[str, Dict]:
    """
    直接返回可注册的工具字典，格式与 tool_registry 一致
    """
    tool_name = "get_history_by_round"
    description = "返回指定轮数的完整历史信息"
    parameters = {
        "round": {
            "type": "integer",
            "description": "要查询的轮数"
        }
    }

    return {
        tool_name: {
            "func": get_history_by_round_tool(memory),
            "parameters": parameters,
            "description": description
        }
    }

# 使用示例：
# from app.tools.history_tools import register_history_tools
# memory = Memory()
# tool_registry = register_history_tools(memory)


def history_tool_descriptor():
    """
    将 get_history_by_round_tool 封装成 MCP tool 格式描述
    """
    return {
        "tools": [
            {
                "name": "get_history_by_round",
                "description": "返回指定轮数的完整历史信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "round": {
                            "type": "integer",
                            "description": "要查询的轮数"
                        }
                    },
                    "required": ["round"]
                }
            }
        ]
    }
