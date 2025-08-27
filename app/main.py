from fastapi import FastAPI
from routers import agent,user
from common.database import init_db

init_db()  # 确保 User / Tool / Memory 表存在

app = FastAPI()

app.include_router(agent.router)
app.include_router(user.router)
if __name__ == "__main__":
    import uvicorn
    # 使用导入字符串 "main:app" 代替直接传递 app 对象
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)