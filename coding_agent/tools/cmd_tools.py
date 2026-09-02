from typing import Any, Dict
from coding_agent.tools.base import BaseTool
from coding_agent.tools.cmd_ops import run_command

class RunCommandTool(BaseTool):
    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "在本地终端执行命令（支持 Windows/Linux 命令）。注意：执行需要阻塞等待完成，请勿运行持续运行的服务器命令。"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令。"}
            },
            "required": ["command"]
        }

    def execute(self, **kwargs) -> str:
        return run_command(kwargs.get("command"))
