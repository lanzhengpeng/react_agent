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

    def get_combined_history(
        self,
        recent_rounds: int = 5,
        round_separator: str = "\n-------\n",
        summary_start: str = "\n" + "=" * 40 + " 思考过程摘要开始 " + "=" * 40 + "\n",
        summary_end: str = "\n" + "=" * 40 + " 思考过程摘要结束，以下是最近几轮完整思考过程 " + "=" * 40 + "\n"
    ) -> str:
        """
        获取思考过程摘要 + 最近 n 轮完整思考过程
        recent_rounds: 最近多少轮显示完整信息
        """
        total_rounds = len(self.full_history)

        lines = []

        # 历史摘要
        if total_rounds > recent_rounds:
            lines.append(summary_start)
            for s in self.summary_history[:total_rounds - recent_rounds]:
                lines.append(s)
                lines.append(round_separator)  # 摘要之间加分隔
            lines.append(summary_end)

        # 最近 n 轮完整信息
        history_to_use = (
            self.full_history[-recent_rounds:]
            if total_rounds > recent_rounds else self.full_history
        )
        for item in history_to_use:
            line = (
                f"Round {item.get('round')}:\n"
                f"Thought: {item.get('thought', '无')}\n"
                f"Action: {item.get('action', '无')}\n"
                f"ActionInput: {item.get('action_input', '无')}\n"
                f"Observation: {item.get('observation', '无')}"
            )
            lines.append(line)

        return round_separator.join(lines)
