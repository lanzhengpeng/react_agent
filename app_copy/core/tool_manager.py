class ToolManager:
    def __init__(self, tools: dict = None):
        """
        tools: 可选，预先注册好的工具字典
        格式：{ tool_name: { "func": callable, "description": str, "input_schema": dict } }
        """
        self.tools = tools or {}

    def call(self, tool_name, **kwargs):
        """
        调用已注册的工具
        """
        if tool_name not in self.tools:
            return {
                "status": "error",
                "message": f"工具调用失败: Tool '{tool_name}' 未找到，请检查工具名和参数列表"
            }

        func = self.tools[tool_name].get("func")
        if not func:
            return {
                "status": "error",
                "message": f"工具调用失败: Tool '{tool_name}' 没有实现调用函数，请检查工具名和参数列表"
            }

        try:
            result = func(**kwargs)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"工具调用失败: {e}，请检查工具名和参数列表"
            }
