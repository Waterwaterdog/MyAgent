import json
from typing import Dict, List, Any, Optional
from coding_agent.tools.base import BaseTool
from coding_agent.tools.file_tools import ListFilesTool, ReadFileTool, WriteFileTool, EditFileTool, SearchFilesTool
from coding_agent.tools.cmd_tools import RunCommandTool

class ToolRegistry:
    """
    工具注册表，负责管理所有可用的工具实例。
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册一个新工具"""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """根据名称获取工具实例"""
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有已注册的工具"""
        return list(self._tools.values())

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 OpenAI JSON Schema"""
        return [tool.to_openai_tool() for tool in self._tools.values()]

# 初始化全局注册表并注册默认工具
registry = ToolRegistry()
registry.register(ListFilesTool())
registry.register(ReadFileTool())
registry.register(WriteFileTool())
registry.register(EditFileTool())
registry.register(SearchFilesTool())
registry.register(RunCommandTool())

# 为了保持向后兼容性，保留原来的变量和函数
TOOLS_SCHEMA = registry.get_openai_schemas()

def dispatch_tool(tool_name: str, tool_args: str) -> str:
    """
    调度器：使用 ToolRegistry 分发工具调用
    """
    tool = registry.get_tool(tool_name)
    if not tool:
        return f"错误：工具 '{tool_name}' 不存在。"
        
    try:
        kwargs = json.loads(tool_args)
    except json.JSONDecodeError:
        return "错误：工具参数 JSON 解析失败。"
        
    try:
        # 验证参数
        tool.validate(**kwargs)
        # 执行工具
        result = tool.execute(**kwargs)
        return str(result)
    except Exception as e:
        return f"执行工具 '{tool_name}' 时发生异常: {e}"
