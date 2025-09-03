from fastapi import FastAPI
from routers import agent_router, tools_router, user_router,chat_session_router,task_prompt_router
from middleware.auth_middleware import auth_middleware

app = FastAPI()
app.middleware("http")(auth_middleware)
app.include_router(agent_router.router)
app.include_router(tools_router.router)
app.include_router(user_router.router)
app.include_router(chat_session_router.router)
app.include_router(task_prompt_router.router)
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # 使用导入字符串 "main:app" 代替直接传递 app 对象
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
