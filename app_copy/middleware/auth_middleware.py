from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from core.auth import SECRET_KEY, ALGORITHM

EXCLUDE_PATHS = ["/user/register", "/user/login", "/docs", "/openapi.json"]  # 排除注册和登录接口

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
        # 如果需要，可以把 payload 或 user_id 附加到 request.state
        request.state.user_payload = payload
    except JWTError:
        return JSONResponse({"detail": "Token 无效或过期"}, status_code=401)

    response = await call_next(request)
    return response
