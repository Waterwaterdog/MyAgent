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
    实现了 Prompt 的静态/动态分离以优化 KV Cache。
    """
    def __init__(self, static_prompt: str, dynamic_instructions: str, llm_client: Any = None, token_budget: int = 4000):
        self.static_prompt = static_prompt
        self.dynamic_instructions = dynamic_instructions
        self.llm = llm_client
        self.token_budget = token_budget
        
        # 结构化存储上下文
        self.messages: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None
        self.current_plan: Optional[Dict] = None
        self.long_term_memory: Optional[str] = None
        self.mid_term_memory: Optional[str] = None
        
    def update_plan(self, plan: Dict):
        """更新当前执行计划，作为动态上下文的一部分"""
        self.current_plan = plan

    def update_memory(self, long_term: str = None, mid_term: str = None):
        """更新从中长期记忆中检索出的信息"""
        if long_term is not None:
            self.long_term_memory = long_term
        if mid_term is not None:
            self.mid_term_memory = mid_term

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
        
        # 静态和动态指令部分
        total += estimate_tokens(self.static_prompt)
        total += estimate_tokens(self.dynamic_instructions)
        
        # 计划部分
        if self.current_plan:
            total += estimate_tokens(json.dumps(self.current_plan))
            
        # 记忆部分
        if self.long_term_memory:
            total += estimate_tokens(self.long_term_memory)
        if self.mid_term_memory:
            total += estimate_tokens(self.mid_term_memory)
            
        # 对话历史部分
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += estimate_tokens(content)
            elif isinstance(content, list): 
                total += estimate_tokens(json.dumps(content))
            
            if "tool_calls" in msg:
                total += estimate_tokens(json.dumps(msg["tool_calls"]))
        
        if self.summary:
            total += estimate_tokens(self.summary)
            
        return total

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        组装对话历史，严格遵循稳定性排序以最大化 KV Cache 复用：
        STATIC PREFIX -> DYNAMIC MODE -> LONG_TERM -> MID_TERM -> PLAN -> SUMMARY -> HISTORY
        """
        result = []
        
        # 1. STATIC PREFIX (最稳定)
        result.append({"role": "system", "content": self.static_prompt})
        
        # 2. DYNAMIC MODE INSTRUCTIONS (Session 内稳定)
        result.append({"role": "system", "content": self.dynamic_instructions})
        
        # 3. LONG-TERM MEMORY (极稳定)
        if self.long_term_memory:
            result.append({
                "role": "system",
                "content": f"## 长期知识沉淀 (Long-term Memory)\n{self.long_term_memory}"
            })
            
        # 4. MID-TERM MEMORY (相对稳定)
        if self.mid_term_memory:
            result.append({
                "role": "system",
                "content": f"## 会话状态感知 (Mid-term Memory)\n{self.mid_term_memory}"
            })

        # 5. CURRENT PLAN (可能更新)
        if self.current_plan:
             result.append({
                 "role": "system", 
                 "content": f"## 当前任务计划\n{json.dumps(self.current_plan, ensure_ascii=False, indent=2)}"
             })
        
        # 6. SUMMARY (压缩时更新)
        if self.summary:
            result.append({
                "role": "system", 
                "content": f"以下是此前对话历史的语义摘要：\n{self.summary}"
            })
            
        # 7. DYNAMIC HISTORY (每轮变化)
        result.extend(self.messages)
            
        return result

    def compress(self):
        """
        压缩上下文。
        调用 LLM 对较旧的消息进行总结，并替换这部分消息以节省 Token。
        """
        if not self.llm or len(self.messages) <= 5:
            return

        print(f"\n[系统]: 上下文超过预算 ({self.get_total_tokens()} tokens)，正在触发压缩...")
        
        # 保留最近的 4 条消息
        to_compress = self.messages[:-4]
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
            summary_msg = self.llm.chat([{"role": "user", "content": prompt}])
            new_summary = summary_msg.content
            
            if self.summary:
                merge_prompt = f"Combine the existing summary with the new findings:\nExisting: {self.summary}\nNew: {new_summary}"
                self.summary = self.llm.chat([{"role": "user", "content": merge_prompt}]).content
            else:
                self.summary = new_summary
            
            # 更新消息列表：只保留最近的消息，因为 System Prompts 在 get_messages 中动态生成
            self.messages = keep_recent
            print(f"[系统]: 压缩完成。当前估算 Token: {self.get_total_tokens()}")
            
        except Exception as e:
            print(f"[系统警告]: 上下文压缩失败: {e}")

# 为了兼容性，保留 Memory 别名
Memory = ContextManager
