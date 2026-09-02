import json
from typing import Dict, List, Any, Optional
from coding_agent.tools.base import BaseTool
from coding_agent.tools.file_tools import ListFilesTool, ReadFileTool, WriteFileTool, EditFileTool, SearchFilesTool
from coding_agent.tools.cmd_tools import RunCommandTool
from coding_agent.tools.api_registry import ApiRegistry

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

# 初始化全局注册表并注册默认工具
registry = ToolRegistry()
api_registry = ApiRegistry()

# 文件操作工具
list_files_tool = ListFilesTool()
registry.register(list_files_tool)
api_registry.register(list_files_tool, "列出目录内容", "list_files(path='.')")

read_file_tool = ReadFileTool()
registry.register(read_file_tool)
api_registry.register(read_file_tool, "读取文件内容", "read_file(path='foo.py')")

write_file_tool = WriteFileTool()
registry.register(write_file_tool)
api_registry.register(write_file_tool, "写入或覆盖文件", "write_file(path='foo.py', content='print(\"hello\")')")

edit_file_tool = EditFileTool()
registry.register(edit_file_tool)
api_registry.register(edit_file_tool, "编辑文件", "edit_file(path='foo.py', old_str='hello', new_str='world')")

search_files_tool = SearchFilesTool()
registry.register(search_files_tool)
api_registry.register(search_files_tool, "搜索文件", "search_files(query='hello', path='.')")

# 命令执行工具
run_command_tool = RunCommandTool()
registry.register(run_command_tool)
api_registry.register(run_command_tool, "执行Shell命令", "run_command(command='ls -l')")


# 为了保持向后兼容性，保留原来的变量和函数
TOOLS_SCHEMA = api_registry.get_all_summaries()

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
