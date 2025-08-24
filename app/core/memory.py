# 上下文管理（历史提示词存储）
class Memory:
    def __init__(self):
        self.history = []
    def add(self, item):
        self.history.append(item)
    def get(self):
        return self.history
