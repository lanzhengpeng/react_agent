# app/core/llm.py
from typing import List, Optional
import openai  # 假设你的自研大模型 SDK 和 openai 接口兼容

class LLM:
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.7,
                 base_url: str = None, api_key: str = None):
        self.model_name = model_name
        self.temperature = temperature

        if base_url is None or api_key is None:
            raise ValueError("必须提供 base_url 和 api_key")

        # 初始化客户端
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key
        )

    def generate(self, system_prompt: str, user_prompt: str, history: Optional[List[str]] = None) -> str:
        """
        生成模型输出
        """
        messages = [{"role": "system", "content": system_prompt}]
        for h in history or []:
            messages.append({"role": "user", "content": h})
        messages.append({"role": "user", "content": user_prompt})

        # 调用模型
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content
