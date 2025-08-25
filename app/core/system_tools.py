# app/tools/history_tools.py
from typing import Callable, Dict
from core.memory import Memory

def get_history_by_round_tool(memory: Memory) -> Callable[[int], Dict]:
    """
    返回指定轮数的完整历史信息工具函数
    
    参数:
        memory: Memory 实例，必须实现 get_full_history() -> Dict[int, dict]

    返回:
        func: 可调用函数，参数 round(int)，返回该轮的完整历史信息
    """
    def func(round: int) -> Dict:
        """
        round: 要查询的轮数
        返回该轮的完整历史信息
        """
        full_history = memory.get_full_history()
        return full_history.get(round, {})  # 没有该轮则返回空字典

    return func
