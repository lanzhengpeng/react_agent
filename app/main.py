from fastapi import FastAPI
from routers import agent,user,tool,chat_session
from middleware.auth_middleware import auth_middleware


app = FastAPI()
# 注册中间件
app.middleware("http")(auth_middleware)

app.include_router(agent.router)
app.include_router(user.router)
app.include_router(tool.router)
app.include_router(chat_session.router)
if __name__ == "__main__":
    import uvicorn
    # 使用导入字符串 "main:app" 代替直接传递 app 对象
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)