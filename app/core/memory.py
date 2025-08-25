class Memory:
    def __init__(self):
        # 保存完整历史，每轮是一个 dict
        self.full_history = []
        # 保存摘要历史，每轮是一个字符串
        self.summary_history = []

    def add(self, thought, action, action_input, observation, summary):
        """
        添加一轮交互信息
        """
        round_data = {
            "round": len(self.full_history) + 1,
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation
        }

        self.full_history.append(round_data)
        self.summary_history.append(summary)

    def get_full_history(self):
        """获取完整历史（list）"""
        return self.full_history

    def get_summary_history(self):
        """获取摘要历史（list）"""
        return self.summary_history

    def get_summary_prompt(self):
        """拼接摘要历史成字符串，用于 prompt"""
        parts = []
        for i, summary in enumerate(self.summary_history, start=1):
            parts.append(f"第{i}轮: {summary}")
        return "\n".join(parts)

    def clear(self):
        """清空历史"""
        self.full_history = []
        self.summary_history = []

    def load_context(self, user_prompt: str = "") -> list:
        """
        返回当前历史上下文，供 LLM 使用
        user_prompt: 用户初始任务，可作为第一条历史
        返回一个列表，每条是字符串
        """
        history = []
        if user_prompt:
            history.append(f"用户任务: {user_prompt}")
        # 可以选择拼接摘要或者完整历史，这里默认用摘要
        if self.summary_history:
            history.append(self.get_summary_prompt())
        return history
