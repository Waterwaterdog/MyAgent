from typing import Dict, List, Any, Optional
from coding_agent.tools.base import BaseTool

class ApiRegistry:
    """
    API注册表，负责管理所有可用工具的文档，并支持不同详细程度的文档。
    """
    def __init__(self):
        self._apis: Dict[str, Dict[str, Any]] = {}

    def register(self, tool: BaseTool, summary: str, examples: str = ""):
        """
        注册一个新API。

        Args:
            tool: BaseTool的实例。
            summary: API功能的简短摘要。
            examples: API使用示例。
        """
        self._apis[tool.name] = {
            "tool": tool,
            "summary": summary,
            "full_schema": tool.to_openai_tool(),
            "summary_schema": self._create_summary_schema(tool, summary),
            "examples": examples
        }

    def _create_summary_schema(self, tool: BaseTool, summary: str) -> Dict[str, Any]:
        """创建只包含摘要的schema"""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": summary,
                "parameters": tool.input_schema
            }
        }

    def get_api(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取API信息"""
        return self._apis.get(name)

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """获取所有API的摘要schema"""
        return [api["summary_schema"] for api in self._apis.values()]

    def get_full_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取完整的OpenAI schema"""
        api = self.get_api(name)
        return api["full_schema"] if api else None
