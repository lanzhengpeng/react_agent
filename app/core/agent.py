from core.memory import Memory
from core.tool_manager import ToolManager
from core.llm import LLM
from core.prompts import SYSTEM_PROMPT,USER_PROMPT_TEMPLATE,COMPRESS_PROMPT,TASK_description
from utils.logger import log_step
import json
from core.global_vars import GlobalVars
from core.system_tools import register_history_tools,history_tool_descriptor
from core.user_vars import UserVars
# 获取用户全局管理器实例
uv = UserVars()
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

    # 获取当前用户 ID
    user_id = request.get("user_id")
    if not user_id:
        raise ValueError("request 中必须包含 user_id")

    # 获取 UserVars 单例
    uv = UserVars()

    # 获取当前用户工具
    tools = uv.get(user_id, "tools", {})

    # 注册系统工具（追加，不覆盖）
    tools.update(register_history_tools(memory))

    # 保存回 UserVars
    uv.set(user_id, "tools", tools)

    # 初始化 ToolManager，每个用户独立对象
    tool_manager = uv.get(user_id, "tool_manager")
    if not tool_manager:
        tool_manager = ToolManager(tools)
        uv.set(user_id, "tool_manager", tool_manager)
    else:
        # 如果用户已有 ToolManager，更新工具字典
        tool_manager.tools = tools

    # 获取 LLM
    llm = LLM(base_url="http://112.132.229.234:8029/v1", api_key="qwe")

    # 用户任务和工具信息
    user_task = request.get("task", "")
    tools_info = uv.get(user_id, "tools_info", {})
    tools_info.setdefault("tools", [])
    tools_info["tools"].extend(history_tool_descriptor()["tools"])
    uv.set(user_id, "tools_info", tools_info)

    log_step("Agent started")
    USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
        SafeDict(extra_instructions=user_task, tools_info=tools_info)
    )

    for step in range(max_steps):
        # 1️⃣ 模型生成 Thought / Action / Action Input / Answer
        output = llm.generate(SYSTEM_PROMPT, TASK_description, USER_PROMPT)
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
            return {"result": answer}

        # 3️⃣ 执行 Action 工具
        observation = None
        if action:
            try:
                observation = tool_manager.call(action, **(action_input or {}))
            except Exception as e:
                observation = f"工具调用失败: {e}"

        # 压缩提示词
        compress_prompt = COMPRESS_PROMPT.format_map({"Observation": observation})
        compress_observation = llm.compress_observation(compress_prompt)

        # 4️⃣ 将本轮 Thought/Action/Observation 加入历史
        summary = f"第{step+1}轮:\nThought: {thought}\nAction: {action}\nAction Input: {action_input}\nObservation: {compress_observation}"
        memory.add(thought, action, action_input, observation, summary)

        USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
            SafeDict(
                extra_instructions=user_task,
                tools_info=tools_info,
                latest_history=memory.get_combined_history()
            )
        )

    return {"result": "未得到最终答案，请增加 max_steps 或检查模型输出"}


def parse_llm_output_stream(output_stream):
    """
    流式解析模型输出，先收集所有块，解析后再流式返回 Thought / Action / Action Input / Answer
    """
    # 收集所有流式输入块
    full_output = ""
    for chunk in output_stream:
        full_output += chunk  # 无进度通知，直接收集

    # 使用原始的 parse_llm_output 逻辑解析完整输出
    result = {
        "thought": None,
        "action": None,
        "action_input": None,
        "answer": None
    }
    current_field = None
    field_lines = {"thought": [], "action": [], "action_input": [], "answer": []}

    lines = full_output.split("\n")
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
    if field_lines["action_input"]:
        try:
            result["action_input"] = json.loads("\n".join(field_lines["action_input"]))
        except:
            result["action_input"] = None
    result["answer"] = "\n".join(field_lines["answer"]).strip() or None

    # 流式返回解析结果的每个部分
    if result["thought"]:
        yield {"status": "thought", "value": result["thought"]}
    if result["action"]:
        yield {"status": "action", "value": result["action"]}
    if result["action_input"]:
        yield {"status": "action_input", "value": result["action_input"]}
    if result["answer"]:
        yield {"status": "answer", "value": result["answer"]}


def run_agent_stream(request, max_steps: int = 50):
    """
    流式运行 agent，逐块返回 Thought, Action, Action Input, Observation 和 Answer
    不再返回压缩后的 Observation
    """
    memory = Memory()

    # 获取当前用户 ID
    user_id = request.get("user_id")
    if not user_id:
        yield {"status": "error", "message": "request 中必须包含 user_id"}
        return

    # 获取 UserVars 单例
    uv = UserVars()

    # 获取用户工具
    tools = uv.get(user_id, "tools", {})
    tools.update(register_history_tools(memory))
    uv.set(user_id, "tools", tools)

    # 获取或创建 ToolManager
    tool_manager = uv.get(user_id, "tool_manager")
    if not tool_manager:
        tool_manager = ToolManager(tools)
        uv.set(user_id, "tool_manager", tool_manager)
    else:
        # 更新工具字典
        tool_manager.tools = tools

    # 获取 LLM
    llm = LLM(base_url=request.get("model_url"), api_key=request.get("api_key"))

    # 用户任务和工具信息
    user_task = request.get("task", "")
    tools_info = uv.get(user_id, "tools_info", {})
    tools_info.setdefault("tools", [])
    tools_info["tools"].extend(history_tool_descriptor()["tools"])
    uv.set(user_id, "tools_info", tools_info)

    yield {"status": "info", "message": "Agent 已启动"}
    log_step("Agent started")

    USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
        SafeDict(extra_instructions=user_task, tools_info=tools_info)
    )

    for step in range(max_steps):
        yield {"status": "step", "step": step + 1}
        log_step(f"Step {step + 1}")

        # 1️⃣ 流式获取模型输出并解析
        output_stream = llm.generate_stream(SYSTEM_PROMPT, TASK_description, USER_PROMPT)
        thought, action, action_input, answer = None, None, None, None

        for parsed in parse_llm_output_stream(output_stream):
            yield parsed
            if parsed["status"] == "thought":
                thought = parsed["value"]
            elif parsed["status"] == "action":
                action = parsed["value"]
            elif parsed["status"] == "action_input":
                action_input = parsed["value"]
            elif parsed["status"] == "answer":
                answer = parsed["value"]

        # 2️⃣ 如果有 Answer，保存并返回
        if answer:
            memory.add(thought, action, action_input, None, None)
            yield {"status": "final", "result": answer}
            return

        # 3️⃣ 行动 Action 工具
        observation = None
        if action:
            try:
                observation = tool_manager.call(action, **(action_input or {}))
                yield {"status": "observation", "value": observation}
                log_step(f"Observation: {observation}")
            except Exception as e:
                observation = f"工具调用失败: {e}"
                yield {"status": "error", "message": observation}
                log_step(f"Observation: {observation}")

        # 4️⃣ 更新历史记录
        summary = f"第{step+1}轮:\nThought: {thought or '无'}\nAction: {action or '无'}\nAction Input: {action_input or '无'}\nObservation: {observation or '无'}"
        memory.add(thought, action, action_input, observation, summary)

        # 5️⃣ 更新 USER_PROMPT
        USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
            SafeDict(extra_instructions=user_task,
                     tools_info=tools_info,
                     latest_history=memory.get_combined_history())
        )

    yield {"status": "final", "result": "未得到最终答案，请增加 max_steps 或检查模型输出"}
