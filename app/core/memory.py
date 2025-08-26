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

    def clear(self):
        """清空历史"""
        self.full_history = []
        self.summary_history = []

    def get_combined_history(self, recent_rounds: int = 5) -> str:
        """
        获取组合历史文本：
        - 最近 recent_rounds 轮保持完整信息
        - 更早轮次只保留摘要
        - 返回字符串，可直接喂给大模型
        """
        total_rounds = len(self.full_history)
        lines = []

        if total_rounds <= recent_rounds:
            # 不足 recent_rounds，全都保留完整
            history_to_use = self.full_history
        else:
            # 更早轮次只保留摘要
            lines.extend(self.summary_history[:total_rounds - recent_rounds])
            history_to_use = self.full_history[-recent_rounds:]

        # 处理最近几轮完整信息
        for item in history_to_use:
            line = f"Round {item.get('round')}: Thought: {item.get('thought')}, Action: {item.get('action')}, ActionInput: {item.get('action_input')}, Observation: {item.get('observation')}"
            lines.append(line)

        # 返回拼接后的文本
        return "\n".join(lines)


