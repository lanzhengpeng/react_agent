# services/user_service.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.user_model import User
from core.auth import create_access_token
import openai

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: Session):
        self.db = db

    # 注册用户
    def register_user(self, username: str, password: str, api_key: str = None, model_url: str = None):
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("用户名已存在")

        hashed_password = pwd_context.hash(password)
        user = User(
            username=username,
            hashed_password=hashed_password,
            api_key=api_key,
            model_url=model_url
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # 登录用户
    def login_user(self, username: str, password: str):
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise ValueError("用户名或密码错误")
        access_token = create_access_token(data={"user_id": user.id, "username": user.username})
        return access_token

    # 更新模型信息
    def update_model_info(self, user_id: int, api_key: str, model_url: str, model_name: str):
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 测试模型是否可用
        client = openai.OpenAI(base_url=model_url, api_key=api_key)
        try:
            client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "测试"}],
                max_tokens=1
            )
        except Exception as e:
            raise ValueError(f"api_key 或 model_url 或 model_name 无效: {e}")

        # 测试通过才更新
        user.api_key = api_key
        user.model_url = model_url
        user.model_name = model_name
        self.db.commit()
        self.db.refresh(user)
        return user
