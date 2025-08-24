# 工具调用统一管理
class ToolManager:
    def __init__(self):
        self.tools = {}
    def register(self, name, func):
        self.tools[name] = func
    def call(self, name, *args, **kwargs):
        if name in self.tools:
            return self.tools[name](*args, **kwargs)
        raise Exception(f"Tool {name} not found")
