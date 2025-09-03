# controllers/task_prompt_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from models.user_model import User
from services.task_prompt_service import TaskPromptService
from schemas.task_prompt_schema import SavePromptRequest, SavePromptResponse
from schemas.agent_schema import TaskStepPromptResponse
from services.agent_service import Agent
router = APIRouter(prefix="/prompt", tags=["prompt"])

@router.post("/save", response_model=SavePromptResponse)
def save_task_prompt(request: SavePromptRequest,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    service = TaskPromptService(db)
    try:
        service.save_prompt(current_user.id, request.prompt)
        return SavePromptResponse(success=True, message="提示词已保存到数据库")
    except Exception as e:
        return SavePromptResponse(success=False, message=f"保存失败: {e}")

# ===== 从数据库加载提示词到内存 =====
@router.post("/load_task_step_prompt", response_model=TaskStepPromptResponse)
def load_task_step_prompt_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TaskPromptService(db)
    try:
        service.load_task_step_prompt(current_user.id)
        return TaskStepPromptResponse(success=True, message="提示词已加载到内存")
    except ValueError as ve:
        return TaskStepPromptResponse(success=False, message=str(ve))
    except Exception as e:
        return TaskStepPromptResponse(success=False, message=f"加载失败: {e}")
