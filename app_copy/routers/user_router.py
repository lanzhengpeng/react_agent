# controllers/user_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from core.database import get_db
from models.user_model import User
from core.auth import get_current_user
from services.user_service import UserService
from schemas.user_schema import RegisterRequest,UpdateModelRequest,LoginRequest
router = APIRouter(prefix="/user", tags=["user"])

# ---------------- Controller ----------------
@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        user = service.register_user(
            username=request.username,
            password=request.password,
            api_key=request.api_key,
            model_url=request.model_url
        )
        return {"message": "注册成功", "user_id": user.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        token = service.login_user(request.username, request.password)
        return {"message": "登录成功", "access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.put("/update_model_info")
def update_model_info(
    request: UpdateModelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    try:
        user = service.update_model_info(
            user_id=current_user.id,
            api_key=request.api_key,
            model_url=request.model_url,
            model_name=request.model_name
        )
        return {
            "message": "更新成功",
            "api_key": "********",
            "model_url": user.model_url,
            "model_name": user.model_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
