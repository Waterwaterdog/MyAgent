import json
import os
from typing import List, Dict, Any, Optional

class MemoryManager:
    """
    分层记忆管理器 (Memory Manager)。
    支持三层记忆：
    1. Short-term: 由 ContextManager 维护的对话历史。
    2. Mid-term: 当前会话的项目规范、决策、进度（Session-level）。
    3. Long-term: 跨会话的用户偏好、长期知识（Persistent）。
    """
    def __init__(self, llm_client: Any = None, storage_path: str = "logs/long_term_memory.json"):
        self.llm = llm_client
        self.storage_path = storage_path
        
        # Mid-term memory: 在内存中维护
        self.mid_term: Dict[str, Any] = {
            "project_conventions": [],
            "key_decisions": [],
            "known_errors": [],
            "current_progress": ""
        }
        
        # Long-term memory: 从文件加载
        self.long_term: Dict[str, Any] = self._load_long_term()

    def _load_long_term(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"user_preferences": [], "reusable_knowledge": []}
        return {"user_preferences": [], "reusable_knowledge": []}

    def save_long_term(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.long_term, f, ensure_ascii=False, indent=2)

    def update_mid_term(self, key: str, value: Any):
        if key in self.mid_term:
            if isinstance(self.mid_term[key], list):
                if value not in self.mid_term[key]:
                    self.mid_term[key].append(value)
            else:
                self.mid_term[key] = value

    def update_long_term(self, key: str, value: Any):
        if key in self.long_term:
            if isinstance(self.long_term[key], list):
                if value not in self.long_term[key]:
                    self.long_term[key].append(value)
            else:
                self.long_term[key] = value
        self.save_long_term()

    def extract_insights(self, messages: List[Dict[str, Any]]):
        """
        利用 LLM 从最近的对话中提取记忆点（Insights）。
        """
        if not self.llm or len(messages) < 2:
            return

        # 只对最近的对话进行分析，避免 Token 浪费
        recent_context = json.dumps(messages[-10:], ensure_ascii=False)
        
        prompt = (
            "Analyze the following conversation and tool execution history. "
            "Extract any new project conventions, key decisions, known errors, or user preferences. "
            "Return the results in a strict JSON format with keys: "
            "'mid_term_insights' (list of strings for conventions/decisions/errors) and "
            "'long_term_preferences' (list of strings for user preferences).\n\n"
            f"History: {recent_context}"
        )
        
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            # 尝试解析 JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            
            insights = json.loads(content)
            
            for insight in insights.get("mid_term_insights", []):
                # 简单分类存入 mid_term
                if "error" in insight.lower():
                    self.update_mid_term("known_errors", insight)
                elif "decision" in insight.lower() or "decided" in insight.lower():
                    self.update_mid_term("key_decisions", insight)
                else:
                    self.update_mid_term("project_conventions", insight)
            
            for pref in insights.get("long_term_preferences", []):
                self.update_long_term("user_preferences", pref)
                
        except Exception as e:
            print(f"[系统警告]: 记忆提取失败: {e}")

    def get_mid_term_context(self) -> str:
        """获取中期记忆上下文"""
        parts = []
        if any(self.mid_term.values()):
            parts.append("## Session Insights (Mid-term Memory)")
            if self.mid_term["project_conventions"]:
                parts.append("- Conventions: " + "; ".join(self.mid_term["project_conventions"]))
            if self.mid_term["key_decisions"]:
                parts.append("- Key Decisions: " + "; ".join(self.mid_term["key_decisions"]))
            if self.mid_term["known_errors"]:
                parts.append("- Known Errors to Avoid: " + "; ".join(self.mid_term["known_errors"]))
            if self.mid_term["current_progress"]:
                parts.append(f"- Progress: {self.mid_term['current_progress']}")
        return "\n".join(parts)

    def get_long_term_context(self) -> str:
        """获取长期记忆上下文"""
        parts = []
        if self.long_term["user_preferences"] or self.long_term["reusable_knowledge"]:
            parts.append("## Persistent Knowledge (Long-term Memory)")
            if self.long_term["user_preferences"]:
                parts.append("- User Preferences: " + "; ".join(self.long_term["user_preferences"]))
            if self.long_term["reusable_knowledge"]:
                parts.append("- Reusable Knowledge: " + "; ".join(self.long_term["reusable_knowledge"]))
        return "\n".join(parts)

    def get_memory_context(self) -> str:
        """获取组装好的完整记忆上下文 (为了向后兼容)"""
        long_term = self.get_long_term_context()
        mid_term = self.get_mid_term_context()
        return "\n\n".join(filter(None, [long_term, mid_term]))
