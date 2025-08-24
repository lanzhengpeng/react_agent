class Memory:
    def __init__(self):
        # 保存完整历史，每轮是一个 dict
        self.full_history = {}
        # 保存摘要历史，每轮是一个 dict
        self.summary_history = {}

        # 当前轮数
        self.round = 0

    def add(self, thought, action, action_input, observation, summary):
        """
        添加一轮交互信息
        :param thought: 模型思考
        :param action: 执行动作
        :param action_input: 动作输入
        :param observation: 动作结果
        :param summary: 本轮的压缩摘要（可用另一模型生成）
        """
        self.round += 1

        # 保存完整信息
        self.full_history[self.round] = {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation
        }

        # 保存摘要信息
        self.summary_history[self.round] = summary

    def get_full_history(self):
        """获取完整历史"""
        return self.full_history

    def get_summary_history(self):
        """获取摘要历史"""
        return self.summary_history

    def get_summary_prompt(self):
        """拼接摘要历史成字符串，用于 prompt"""
        parts = []
        for r, summary in self.summary_history.items():
            parts.append(f"第{r}轮: {summary}")
        return "\n".join(parts)
