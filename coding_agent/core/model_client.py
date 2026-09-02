import os
from openai import OpenAI

class LLMClient:
    """
    对大模型 API 的封装，使用 OpenAI 官方 Python SDK。
    负责与 LLM 通信并返回结果。
    """
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")  # 允许配置自定义的 Base URL
        if not api_key:
            raise ValueError("环境变量 OPENAI_API_KEY 未设置！请检查 .env 文件。")
            
        # 如果配置了 base_url（如阿里云百炼），则传入 client
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0, max_retries=2)
        else:
            self.client = OpenAI(api_key=api_key, timeout=120.0, max_retries=2)
            
        # 默认使用 gpt-4o-mini，可被环境变量覆盖为 qwen-max, deepseek-chat 等
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def chat(self, messages, tools=None):
        """
        发送聊天请求到 LLM。
        """
        params = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            params["tools"] = tools
            # 让模型自动决定是否调用工具
            params["tool_choice"] = "auto"
            
        response = self.client.chat.completions.create(**params)
        # 返回第一项候选结果的 message 对象 (ChatCompletionMessage)
        return response.choices[0].message


class MockLLMClient(LLMClient):
    def __init__(self, tool_calls=None, content=None):
        self.tool_calls = tool_calls
        self.content = content
        self.first_call = True
        self.model = "mock-model"

    def chat(self, messages, tools=None):
        from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
        from openai.types.chat.chat_completion_message_tool_call import Function

        if self.first_call and self.tool_calls:
            self.first_call = False
            tool_calls_obj = []
            for tc in self.tool_calls:
                tool_calls_obj.append(
                    ChatCompletionMessageToolCall(
                        id=tc["id"],
                        function=Function(arguments=tc["function"]["arguments"], name=tc["function"]["name"]),
                        type='function'
                    )
                )
            return ChatCompletionMessage(role="assistant", tool_calls=tool_calls_obj, content=self.content)
        else:
            return ChatCompletionMessage(role="assistant", content=self.content or "任务完成")
