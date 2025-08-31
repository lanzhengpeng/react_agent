from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from models.chat_session_model import ChatSession
from models.user_model import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./database/react_agent.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 确保模型类被绑定到 Base
Base.metadata.create_all(bind=engine)

# 获取数据库 session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
