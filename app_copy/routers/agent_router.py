from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.agent_schema import AgentRequest, AgentResponse,TaskStepPromptRequest,TaskStepPromptResponse
from services.agent_service import Agent
from core.database import get_db  # 你的 get_db 函数
from models.user_model import User
from core.auth import get_current_user
import json
from fastapi.responses import StreamingResponse
router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/run_agent_stream")
def run_agent_stream_endpoint(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):  # ✅ 先获取真实 Session):
    """
    流式运行 Agent 的 API 端点，返回 SSE 格式的流式响应
    """
    print("收到流式请求:", request.dict())

    def event_stream():
        # 校验用户的 api_key 和 model_url
        if not current_user.api_key or not current_user.model_url:
            error_event = {
                "status": "error",
                "message": "用户未提供 api_key 或 model_url"
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            return

        # 创建 Agent
        agent = Agent(
            user_id=current_user.id,
            db=db,  # ✅ 传入实际 Session
            model_config={
                "model_name": current_user.model_name,
                "model_url": current_user.model_url,
                "api_key": current_user.api_key
            })

        # 调用 run_stream 获取生成器
        for event in agent.run_stream(request.task):
            if isinstance(event, dict):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            else:
                error_event = {
                    "status": "error",
                    "message": f"意外的事件格式: {type(event)}"
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(),
                             media_type="text/event-stream; charset=utf-8")
# ------------------ 设置用户任务步骤提示词 ------------------


@router.post("/set_task_step_prompt", response_model=TaskStepPromptResponse)
def set_task_step_prompt_endpoint(
    request: TaskStepPromptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  # ✅ 加上 db
):
    """
    设置当前用户的任务步骤提示词，后续 run_agent 或 run_agent_stream 会使用
    """
    try:
        agent = Agent(user_id=current_user.id, db=db)  # ✅ 传入 db
        agent.set_task_step_prompt(request.task_step_prompt)  # 具体实现放到 Agent 类里
        return TaskStepPromptResponse(success=True, message="任务步骤提示词已保存")
    except Exception as e:
        return TaskStepPromptResponse(success=False, message=f"保存失败: {e}")

