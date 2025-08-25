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
            raise Exception(f"Tool {tool_name} not found")

        func = self.tools[tool_name].get("func")
        if not func:
            raise Exception(f"Tool {tool_name} 没有实现调用函数")

        return func(**kwargs)
