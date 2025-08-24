from app.core.memory import Memory
from app.core.tool_manager import ToolManager
from app.core.llm import LLM
from app.core.prompts import SYSTEM_PROMPT
from app.utils.logger import log_step
import json

def parse_llm_output(output: str) -> dict:
    """
    解析模型输出成 Thought / Action / Action Input / Answer
    """
    result = {
        "thought": None,
        "action": None,
        "action_input": None,
        "answer": None
    }

    lines = output.split("\n")
    for line in lines:
        if line.startswith("Thought:"):
            result["thought"] = line[len("Thought:"):].strip()
        elif line.startswith("Action:"):
            result["action"] = line[len("Action:"):].strip()
        elif line.startswith("Action Input:"):
            try:
                result["action_input"] = json.loads(line[len("Action Input:"):].strip())
            except:
                result["action_input"] = None
        elif line.startswith("Answer:"):
            result["answer"] = line[len("Answer:"):].strip()
    return result

def run_agent(request, max_steps: int = 5):
    memory = Memory()
    tool_manager = ToolManager()
    llm = LLM()  # 你的 LLM 封装

    user_prompt = request.get("task", "")
    log_step("Agent started")
    
    # 初始化上下文历史
    history = memory.load_context(user_prompt)

    for step in range(max_steps):
        # 1️⃣ 模型生成 Thought / Action / Action Input / Answer
        output = llm.generate(SYSTEM_PROMPT, user_prompt, history)
        parsed = parse_llm_output(output)

        thought = parsed["thought"]
        action = parsed["action"]
        action_input = parsed["action_input"]
        answer = parsed["answer"]

        log_step(f"Step {step + 1}")
        log_step(f"Thought: {thought}")
        log_step(f"Action: {action}")
        log_step(f"Action Input: {action_input}")
        log_step(f"Answer: {answer}")

        # 2️⃣ 如果模型已经输出最终答案，终止循环
        if answer:
            memory.save_context(user_prompt, history)
            return {"result": answer}

        # 3️⃣ 执行 Action 工具
        observation = None
        if action:
            try:
                observation = tool_manager.call(action, **(action_input or {}))
            except Exception as e:
                observation = f"工具调用失败: {e}"

        # 4️⃣ 将本轮 Thought/Action/Observation 加入历史
        step_record = f"Thought: {thought}\nAction: {action}\nAction Input: {action_input}\nObservation: {observation}"
        history.append(step_record)

    memory.save_context(user_prompt, history)
    return {"result": "未得到最终答案，请增加 max_steps 或检查模型输出"}
