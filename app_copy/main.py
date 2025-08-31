from fastapi import FastAPI
from routers import agent_router
app = FastAPI()
app.include_router(agent_router.router)
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # 使用导入字符串 "main:app" 代替直接传递 app 对象
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
