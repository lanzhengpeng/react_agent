from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from common.auth import SECRET_KEY, ALGORITHM, get_current_user
from sqlalchemy.orm import Session
from common.database import get_db

EXCLUDE_PATHS = ["/user/register", "/user/login","/docs","/openapi.json"]  # 排除注册和登录接口

async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path in EXCLUDE_PATHS:
        # 排除注册和登录
        response = await call_next(request)
        return response

    # 获取 Authorization Header
    auth: str = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return JSONResponse({"detail": "未提供 token"}, status_code=401)

    token = auth[len("Bearer "):]

    # 验证 token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise JWTError
    except JWTError:
        return JSONResponse({"detail": "Token 无效或过期"}, status_code=401)

    # 可以附加当前用户到 request.state
    db: Session = next(get_db())
    from models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse({"detail": "用户不存在"}, status_code=401)

    request.state.current_user = user

    response = await call_next(request)
    return response
