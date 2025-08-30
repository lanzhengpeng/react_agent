from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from common.database import get_db
from models.user import User
from pydantic import BaseModel
from typing import Optional
from common.auth import create_access_token
from common.auth import get_current_user
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
    
    # 登录失败返回 401
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(data={"user_id": user.id, "username": user.username})
    return {
        "message": "登录成功",
        "access_token": access_token,
        "token_type": "bearer"
    }
# 请求体，只需要 api_key 和 model_url model_name
class UpdateModelRequest(BaseModel):
    api_key: str
    model_url: str
    model_name: str  # 新增字段

from fastapi import HTTPException

@router.put("/update_model_info")
def update_model_info(
    request: UpdateModelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户的 api_key、model_url 和 model_name
    并在更新前测试是否可用
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 测试模型是否可用
    import openai
    client = openai.OpenAI(base_url=request.model_url, api_key=request.api_key)
    try:
        response = client.chat.completions.create(
            model=request.model_name,
            messages=[{"role": "user", "content": "测试"}],
            max_tokens=1
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"api_key 或 model_url 或 model_name 无效: {e}")

    # 如果测试通过，才更新数据库
    user.api_key = request.api_key
    user.model_url = request.model_url
    user.model_name = request.model_name
    db.commit()
    db.refresh(user)

    return {"message": "更新成功", "api_key": "********", "model_url": user.model_url, "model_name": user.model_name}
