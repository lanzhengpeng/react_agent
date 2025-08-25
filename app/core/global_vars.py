# core/global_vars.py

class GlobalVars:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._vars = {}
        return cls._instance

    def set(self, key, value):
        self._vars[key] = value

    def get(self, key, default=None):
        return self._vars.get(key, default)

    def all(self):
        return self._vars

# 用法示例：
# from core.global_vars import GlobalVars
# gv = GlobalVars()
# gv.set("tool_manager", tool_manager)
# tm = gv.get("tool_manager")
