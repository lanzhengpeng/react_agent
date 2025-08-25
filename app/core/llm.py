# app/core/llm.py
from typing import List, Optional
import openai  # 假设你的自研大模型 SDK 和 openai 接口兼容

class LLM:
    def __init__(self, model_name: str = "DeepSeek-R1-Distill-Qwen-671B", temperature: float = 0.7,
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

    def generate(self, system_prompt: str, assistant_prompt: str, user_prompt: str) -> str:
        """
        生成模型输出
        system_prompt: 系统规则/输出格式
        assistant_prompt: 固定操作步骤/行为准则
        user_prompt: 用户任务、历史摘要、最近历史、工具信息
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": assistant_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 调用模型
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content

