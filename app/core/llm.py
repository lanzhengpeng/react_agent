# app/core/llm.py
from typing import Generator
import openai  # 假设你的自研大模型 SDK 和 openai 接口兼容


class LLM:

    def __init__(self,
                 model_name: str = "DeepSeek-R1-Distill-Qwen-671B",
                 temperature: float = 0.7,
                 base_url: str = None,
                 api_key: str = None):
        self.model_name = model_name
        self.temperature = temperature

        if base_url is None or api_key is None:
            raise ValueError("必须提供 base_url 和 api_key")

        # 初始化客户端
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)

    # 同步生成（保留原方法）
    def generate(self, system_prompt: str, assistant_prompt: str,
                 user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": assistant_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content

    # 假设这是 LLM 类的一部分
    def generate_stream(self, system_prompt: str, assistant_prompt: str, user_prompt: str):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": assistant_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 直接使用 client 的流式接口
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            temperature=self.temperature,
        )

        for chunk in stream:
            # 判断 delta.content 是否存在
            delta_content = getattr(chunk.choices[0].delta, "content", None)
            if delta_content is not None:
                yield delta_content


    # Observation 压缩保持同步
    def compress_observation(self, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": "你是一个信息压缩助手"},
            {"role": "assistant", "content": "请根据提示词对 Observation 进行压缩"},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content
