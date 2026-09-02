import subprocess
import os
from ..core.error import AgentError

# 导入 file_ops 中的沙箱路径
from coding_agent.tools.file_ops import WORKSPACE_DIR

# 高危命令黑名单，拦截明显具有破坏性的命令
FORBIDDEN_COMMANDS = [
    "rm -rf", "mkfs", "dd", "format", "> /dev/sda", 
    "shutdown", "reboot", "init"
]

def run_command(command: str) -> str:
    """在沙箱工作目录内执行本地终端命令，返回标准输出和标准错误。"""
    
    # 简单的安全检查：拦截黑名单命令
    cmd_lower = command.lower()
    for forbidden in FORBIDDEN_COMMANDS:
        if forbidden in cmd_lower:
            raise AgentError(
                code="E_COMMAND_FAILED",
                type="CommandError",
                message=f"安全拦截：禁止执行包含 '{forbidden}' 的危险命令。",
                retryable=False
            )
            
    try:
        # 使用 subprocess.run 执行命令
        # 设置 cwd 为沙箱目录，限制默认执行路径
        # timeout 设置为 10 秒，防止命令（如 ping 或启动服务器）导致 Agent 无限等待
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # 拼接输出
        output = ""
        if result.stdout:
            output += f"[STDOUT]\n{result.stdout}\n"
        if result.stderr:
            output += f"[STDERR]\n{result.stderr}\n"
            
        if not output:
            output = "[执行完成，无输出]"
            
        output = f"Exit Code: {result.returncode}\n" + output
        
        # 截断过长的输出，保护上下文
        if len(output) > 5000:
            return output[:5000] + "\n...[输出过长已截断]..."
        return output
        
    except subprocess.TimeoutExpired:
        raise AgentError(
            code="E_COMMAND_TIMEOUT",
            type="CommandError",
            message="命令执行超时 (超过10秒)。后台进程可能仍在运行，但 Agent 已停止等待。",
            retryable=True,
            suggested_actions=["Retry the command.", "Increase the timeout."]
        )
    except Exception as e:
        raise AgentError(
            code="E_COMMAND_FAILED",
            type="CommandError",
            message=f"命令执行发生异常: {e}",
            details=str(e),
            retryable=False,
            suggested_actions=["Check the command for errors.", "Inspect the command's output for more details."]
        )
