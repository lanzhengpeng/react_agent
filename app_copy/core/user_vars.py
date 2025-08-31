# core/user_vars.py

import threading

class UserVars:
    _instance = None
    _lock = threading.Lock()  # 加锁

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_vars = {}  # {user_id: {key: value}}
        return cls._instance

    def set(self, user_id, key, value):
        """为指定用户设置变量"""
        with self._lock:
            if user_id not in self._user_vars:
                self._user_vars[user_id] = {}
            self._user_vars[user_id][key] = value

    def get(self, user_id, key, default=None):
        """获取指定用户的变量"""
        with self._lock:
            return self._user_vars.get(user_id, {}).get(key, default)

    def all(self, user_id):
        """获取指定用户的所有变量"""
        with self._lock:
            return self._user_vars.get(user_id, {})

    def remove_user(self, user_id):
        """删除指定用户的所有变量"""
        with self._lock:
            if user_id in self._user_vars:
                del self._user_vars[user_id]

