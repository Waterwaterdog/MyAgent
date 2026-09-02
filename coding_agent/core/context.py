class Memory:
    """
    上下文管理模块。负责存储对话历史、工具调用记录，并控制上下文长度等。
    """
    def __init__(self, system_prompt: str):
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def add_message(self, role: str, content: str = None, **kwargs):
        """通用消息追加方法"""
        msg = {"role": role}
        if content is not None:
            msg["content"] = content
        msg.update(kwargs)
        self.messages.append(msg)

    def add_assistant_message(self, response_message):
        """将 LLM 的返回对象 (ChatCompletionMessage) 转换为字典并存入内存"""
        # exclude_none=True 防止产生值为 None 的字段导致 API 报错
        msg = response_message.model_dump(exclude_none=True)
        self.messages.append(msg)

    def add_tool_message(self, tool_call_id: str, content: str):
        """记录工具执行的返回结果"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def get_messages(self):
        """获取完整的对话历史列表"""
        return self.messages