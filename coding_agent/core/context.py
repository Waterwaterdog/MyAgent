import json
from typing import List, Dict, Any, Optional

def estimate_tokens(text: str) -> int:
    """
    简单的 Token 估算函数。
    对于英文，约 4 个字符一个 Token；对于中文，约 1 个字符 0.75-1 个 Token。
    这里采用保守估计：(中文字符数 * 1.5 + 英文字符数 / 3)
    """
    if not text:
        return 0
    
    # 粗略计算：中文字符（非 ASCII）按 1.5 token，英文字符按 0.33 token
    non_ascii = len([c for c in text if ord(c) > 127])
    ascii_chars = len(text) - non_ascii
    return int(non_ascii * 1.5 + ascii_chars / 3) + 1

class ContextManager:
    """
    高级上下文管理模块（原 Memory 模块的演进）。
    负责存储对话历史、Token 预算管理、上下文压缩（总结）等。
    """
    def __init__(self, system_prompt: str, llm_client: Any = None, token_budget: int = 4000):
        self.system_prompt = system_prompt
        self.llm = llm_client
        self.token_budget = token_budget
        
        # 结构化存储上下文
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.summary: Optional[str] = None
        
    def add_message(self, role: str, content: str = None, **kwargs):
        """通用消息追加方法"""
        msg = {"role": role}
        if content is not None:
            msg["content"] = content
        msg.update(kwargs)
        self.messages.append(msg)

    def add_assistant_message(self, response_message):
        """将 LLM 的返回对象转换为字典并存入内存"""
        msg = response_message.model_dump(exclude_none=True)
        self.messages.append(msg)

    def add_tool_message(self, tool_call_id: str, content: str):
        """记录工具执行的返回结果"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def get_total_tokens(self) -> int:
        """估算当前上下文的总 Token 数"""
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += estimate_tokens(content)
            elif isinstance(content, list): # 处理 multi-modal 或复杂格式
                total += estimate_tokens(json.dumps(content))
            
            # 处理 tool_calls 字段
            if "tool_calls" in msg:
                total += estimate_tokens(json.dumps(msg["tool_calls"]))
        
        if self.summary:
            total += estimate_tokens(self.summary)
            
        return total

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取组装好的对话历史。
        如果存在总结，会将总结插入到 system prompt 之后。
        """
        result = []
        if self.messages:
            result.append(self.messages[0]) # System prompt
            
            if self.summary:
                result.append({
                    "role": "system", 
                    "content": f"Here is a summary of the previous conversation to save context:\n{self.summary}"
                })
            
            # 添加剩余消息（排除已总结的，如果实现了部分总结的话）
            # 目前简单实现为保留所有，但在 Agent 侧触发 compress
            result.extend(self.messages[1:])
            
        return result

    def compress(self):
        """
        压缩上下文。
        调用 LLM 对较旧的消息进行总结，并替换这部分消息以节省 Token。
        """
        if not self.llm or len(self.messages) <= 5:
            return

        print(f"\n[系统]: 上下文超过预算 ({self.get_total_tokens()} tokens)，正在触发压缩...")
        
        # 保留最近的 4 条消息（通常是最近的一轮对话）
        to_compress = self.messages[1:-4]
        keep_recent = self.messages[-4:]
        
        if not to_compress:
            return

        prompt = (
            "Please summarize the following conversation history and tool execution results concisely. "
            "Focus on the key progress made, findings, and current state. "
            "Keep the summary under 500 words.\n\n"
            f"{json.dumps(to_compress, ensure_ascii=False)}"
        )
        
        try:
            # 使用 LLM 进行总结
            # 注意：这里我们使用一个简单的 chat 调用，不带工具
            summary_msg = self.llm.chat([{"role": "user", "content": prompt}])
            new_summary = summary_msg.content
            
            if self.summary:
                # 如果已有总结，则合并
                merge_prompt = f"Combine the existing summary with the new findings:\nExisting: {self.summary}\nNew: {new_summary}"
                self.summary = self.llm.chat([{"role": "user", "content": merge_prompt}]).content
            else:
                self.summary = new_summary
            
            # 更新消息列表：保留 system prompt 和最近的消息
            self.messages = [self.messages[0]] + keep_recent
            print(f"[系统]: 压缩完成。当前估算 Token: {self.get_total_tokens()}")
            
        except Exception as e:
            print(f"[系统警告]: 上下文压缩失败: {e}")

# 为了兼容性，保留 Memory 别名
Memory = ContextManager
