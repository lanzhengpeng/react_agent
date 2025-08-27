from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from common.database import get_db
from models.user import User
from pydantic import BaseModel
from typing import Optional
from common.auth import create_access_token

router = APIRouter(prefix="/user", tags=["user"])
# 加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    username: str
    password: str
    api_key: Optional[str] = None      # 对应 User.api_key，可选
    model_url: Optional[str] = None    # 对应 User.model_url，可选

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 检查用户名是否存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 密码加密
    hashed_password = pwd_context.hash(request.password)

    # 创建用户
    user = User(username=request.username,
                hashed_password=hashed_password,
                api_key=request.api_key,
                model_url=request.model_url)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "注册成功", "user_id": user.id}

# 登录请求体
class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    access_token = create_access_token(data={"user_id": user.id, "username": user.username})
    return {
        "message": "登录成功",
        "access_token": access_token,
        "token_type": "bearer"
    }
