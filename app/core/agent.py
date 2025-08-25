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
    解析模型输出成 Thought / Action / Action Input / Answer，多行内容也能解析
    """
    result = {
        "thought": None,
        "action": None,
        "action_input": None,
        "answer": None
    }

    current_field = None
    field_lines = {"thought": [], "action": [], "action_input": [], "answer": []}

    lines = output.split("\n")
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("Thought:"):
            current_field = "thought"
            field_lines[current_field].append(line_strip[len("Thought:"):].strip())
        elif line_strip.startswith("Action:"):
            current_field = "action"
            field_lines[current_field].append(line_strip[len("Action:"):].strip())
        elif line_strip.startswith("Action Input:"):
            current_field = "action_input"
            field_lines[current_field].append(line_strip[len("Action Input:"):].strip())
        elif line_strip.startswith("Answer:"):
            current_field = "answer"
            field_lines[current_field].append(line_strip[len("Answer:"):].strip())
        else:
            if current_field:
                field_lines[current_field].append(line_strip)

    # 处理结果
    result["thought"] = "\n".join(field_lines["thought"]).strip() or None
    result["action"] = "\n".join(field_lines["action"]).strip() or None
    # 尝试解析 Action Input
    if field_lines["action_input"]:
        try:
            result["action_input"] = json.loads("\n".join(field_lines["action_input"]))
        except:
            result["action_input"] = None
    result["answer"] = "\n".join(field_lines["answer"]).strip() or None

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
        extra_instructions=user_task,
        tools_info=tools_info
    )
)

    # 初始化上下文历史
    history = memory.load_context(user_task)

    for step in range(max_steps):
        # 1️⃣ 模型生成 Thought / Action / Action Input / Answer
        output = llm.generate(SYSTEM_PROMPT, TASK_description,USER_PROMPT)
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

        print("工具返回结果",observation)
        # 4️⃣ 将本轮 Thought/Action/Observation 加入历史
        step_record = f"第{step+1}轮:\nThought: {thought}\nAction: {action}\nAction Input: {action_input}\nObservation: {observation}"
        history.append(step_record)
        USER_PROMPT=USER_PROMPT_TEMPLATE.format_map(
        SafeDict(
        extra_instructions=user_task,
        tools_info=tools_info,
        latest_history=history
        )
)

        # print("工具返回值：",observation)

    # memory.save_context(user_prompt, history)
    return {"result": "未得到最终答案，请增加 max_steps 或检查模型输出"}
