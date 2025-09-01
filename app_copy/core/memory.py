class Memory:

    def __init__(self):
        # 保存完整历史，每轮是一个 dict
        self.full_history = []
        # 保存摘要历史，每轮是一个字符串
        self.summary_history = []

    def add(self, thought, action, action_input, step_result, observation, summary):
        """
        添加一轮交互信息
        """
        step_data = {
            "step": len(self.full_history) + 1,
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "step_result": step_result,  # 新增字段
            "observation": observation
        }

        self.full_history.append(step_data)
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
            recent_steps: int = 5,
            step_separator: str = "\n-------\n",
            summary_start: str = "\n" + "=" * 40 + " 思考过程摘要开始 " + "=" * 40 + "\n",
            summary_end: str = "\n" + "=" * 40 + " 思考过程摘要结束，以下是最近几步完整思考过程 " + "=" * 40 + "\n"
        ) -> str:
        """
        获取思考过程摘要 + 最近 n 步完整思考过程
        recent_steps: 最近多少步显示完整信息
        """
        total_steps = len(self.full_history)

        lines = []

        # 历史摘要
        if total_steps > recent_steps:
            lines.append(summary_start)
            for s in self.summary_history[:total_steps - recent_steps]:
                lines.append(s)
                lines.append(step_separator)  # 摘要之间加分隔
            lines.append(summary_end)

        # 最近 n 步完整信息
        history_to_use = (
            self.full_history[-recent_steps:]
            if total_steps > recent_steps else self.full_history
        )
        for item in history_to_use:
            line = (
                f"Step {item.get('step')}:\n"
                f"Thought: {item.get('thought', '无')}\n"
                f"Action: {item.get('action', '无')}\n"
                f"ActionInput: {item.get('action_input', '无')}\n"
                f"Step_Result: {item.get('step_result', '无')}\n"
                f"Observation: {item.get('observation', '无')}"
            )
            lines.append(line)

        return step_separator.join(lines)

