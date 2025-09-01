# app/services/agent_service.py
import json
from core.memory import Memory
from core.tool_manager import ToolManager
from core.llm import LLM
from core.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, COMPRESS_PROMPT
from core.user_vars import UserVars
from services.chat_session_service import ChatSessionService
from utils.logger import log_step


class SafeDict(dict):
    def __missing__(self, key):
        return ""


import json

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



class Agent:

    def __init__(self, user_id: str, db, model_config=None):
        self.user_id = user_id
        self.db = db
        self.memory = Memory()
        self.user_vars = UserVars()
        self.uv = UserVars()  # ✅ 初始化 uv
        # 聊天记录服务（每个用户独立）
        self.chat_service = ChatSessionService(user_id, db)

        # 初始化工具（每个 Agent 独立）
        tools = self.user_vars.get(user_id, "tools", {})
        self.tool_manager = ToolManager(tools)  # 直接创建，不需要存回 user_vars

        # 初始化 LLM
        model_config = model_config or {}
        self.llm = LLM(model_name=model_config.get("model_name", "default"),
                       base_url=model_config.get(
                           "model_url", "http://112.132.229.234:8029/v1"),
                       api_key=model_config.get("api_key", "qwe"))

        # 工具信息
        self.tools_info = self.user_vars.get(user_id, "tools_info", "暂无工具")

    # ---------------- 设置任务步骤提示词 ----------------
    def set_task_step_prompt(self, task_step_prompt: str):
        """
        保存当前用户的任务步骤提示词
        """
        try:
            self.uv.set(self.user_id, "task_step_prompt", task_step_prompt)
            return True
        except Exception as e:
            raise RuntimeError(f"保存失败: {e}")

    def run_stream(self, user_task: str, max_steps: int = 50):
        """流式运行 Agent"""

        # 使用服务获取聊天历史，并格式化为多轮对话字符串
        task = self.chat_service.format_history(user_task)

        # 新增用户消息
        self.chat_service.add_record(user_task, "user")

        yield {"status": "info", "message": "Agent 已启动"}

        USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
            SafeDict(task_description=task,
                     tools_info=self.tools_info,
                     thinking_process="暂无思考过程"))

        for step in range(max_steps):
            yield {"status": "step", "step": step + 1}
            log_step(f"Step {step + 1}")
            # 任务步骤提示词
            TASK_STEP_PROMPT = self.user_vars.get(self.user_id,
                                                  "task_step_prompt") or ""
            output_stream = self.llm.generate_stream(SYSTEM_PROMPT,
                                                     TASK_STEP_PROMPT,
                                                     USER_PROMPT)
            # 测试看输入

            thought = action = action_input = answer = None
            # 解析大模型输出
            for parsed in parse_llm_output_stream(output_stream):
                yield parsed
                print(parsed)
                status = parsed["status"]
                value = parsed["value"]
                if status == "thought":
                    thought = value
                elif status == "action":
                    action = value
                elif status == "action_input":
                    action_input = value
                elif status == "answer":
                    answer = value

            if answer and answer != "NONE":
                # 保存 assistant 回复
                self.chat_service.add_record(answer, "assistant")
                yield {"status": "final", "result": answer}
                return

            observation = None
            if action and action != "NONE":
                try:
                    observation = self.tool_manager.call(
                        action, **(action_input or {}))
                    yield {"status": "observation", "value": observation}
                except Exception as e:
                    observation = f"工具调用失败: {e}"
                    yield {"status": "error", "message": observation}

            step_record = (f"第{step+1}步:\n"
                           f"Thought: {thought or '无'}\n"
                           f"Action: {action or '无'}\n"
                           f"Action Input: {action_input or '无'}\n"
                           f"Observation: {observation or '无'}")
            # 使用现有 COMPRESS_PROMPT 作为整理提示词
            organize_prompt = COMPRESS_PROMPT.format_map(
                {"step_record": step_record})
            summary = self.llm.compress_observation(organize_prompt)
            self.memory.add(thought, action, action_input, observation,
                            summary)

            # 更新提示词
            USER_PROMPT = USER_PROMPT_TEMPLATE.format_map(
                SafeDict(task_description=task,
                         tools_info=self.tools_info,
                         thinking_process=self.memory.get_combined_history()))

        self.memory.clear()
        yield {"status": "final", "result": "未得到最终答案，请增加 max_steps 或检查模型输出"}
