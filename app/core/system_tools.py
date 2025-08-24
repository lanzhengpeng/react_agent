def get_history_by_round_tool(memory):
    """
    返回指定轮数的完整历史信息
    memory: Memory 实例
    """
    def func(round: int):
        """
        round: 要查询的轮数
        返回该轮的完整历史信息
        """
        full_history = memory.get_full_history()
        return full_history.get(round, {})  # 没有该轮则返回空字典
    return func
