# app/core/llm.py
from typing import Generator
import openai  # 假设你的自研大模型 SDK 和 openai 接口兼容


class LLM:
    def __init__(self,
                 model_name: str = "",
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
    def compress_observation_stream(self, user_prompt: str):
        """
        流式压缩 Observation，返回逐块生成的压缩结果
        """
        # 构造与原始方法相同的消息结构
        messages = [
            {"role": "system", "content": "你是一个信息压缩助手"},
            {"role": "assistant", "content": "请根据提示词对 Observation 进行压缩"},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # 调用流式 API，假设 client 支持 stream=True
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                stream=True  # 启用流式输出
            )

            # 逐块处理流式响应
            for chunk in response:
                # 提取当前块的内容（根据 API 的具体实现）
                # 假设 chunk.choices[0].delta.content 包含增量内容
                if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if content:  # 确保内容非空
                        yield content
                else:
                    # 如果当前块无内容，通知进度
                    yield {"status": "progress", "message": "正在压缩 Observation..."}

        except Exception as e:
            # 如果流式调用失败，返回错误信息
            yield {"status": "error", "message": f"压缩 Observation 失败: {str(e)}"}

