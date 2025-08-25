from core.memory import Memory
from core.tool_manager import ToolManager
from core.llm import LLM
from core.prompts import SYSTEM_PROMPT,USER_PROMPT_TEMPLATE,TASK_description
from utils.logger import log_step
import json
from core.global_vars import GlobalVars


# 获取全局管理器实例
gv = GlobalVars()
class SafeDict(dict):
    def __missing__(self, key):
        return ""  # 默认返回空字符串


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

    current_field = None
    answer_lines = []

    lines = output.split("\n")
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("Thought:"):
            current_field = "thought"
            result["thought"] = line_strip[len("Thought:"):].strip()
        elif line_strip.startswith("Action:"):
            current_field = "action"
            result["action"] = line_strip[len("Action:"):].strip()
        elif line_strip.startswith("Action Input:"):
            current_field = "action_input"
            try:
                result["action_input"] = json.loads(line_strip[len("Action Input:"):].strip())
            except:
                result["action_input"] = None
        elif line_strip.startswith("Answer:"):
            current_field = "answer"
            answer_lines.append(line_strip[len("Answer:"):].strip())
        else:
            # 如果是 Answer 后续行，也要加入 answer
            if current_field == "answer":
                answer_lines.append(line_strip)

    if answer_lines:
        result["answer"] = "\n".join(answer_lines)

    return result


def run_agent(request, max_steps: int = 50):
    memory = Memory()
    tool_manager = ToolManager(gv.get("tools"))
    llm = LLM(base_url="http://112.132.229.234:8029/v1",api_key="qwe")  # 你的 LLM 封装

    user_task = request.get("task", "")
    tools_info= gv.get("tools_info")
    log_step("Agent started")
    USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
    SafeDict(
        task_description=TASK_description,
        extra_instructions=user_task,
        tools_info=tools_info
    )
)

    # 初始化上下文历史
    history = memory.load_context(user_task)

    for step in range(max_steps):
        # 1️⃣ 模型生成 Thought / Action / Action Input / Answer
        output = llm.generate(SYSTEM_PROMPT, USER_PROMPT)
        parsed = parse_llm_output(output)
        # print("大模型输出",output)

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
            # memory.save_context(user_prompt, history)
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
        # print("工具返回值：",observation)

    # memory.save_context(user_prompt, history)
    return {"result": "未得到最终答案，请增加 max_steps 或检查模型输出"}
