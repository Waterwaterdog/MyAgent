import os
from ..core.error import AgentError

# 获取启动时的工作目录作为沙箱根目录
WORKSPACE_DIR = os.path.abspath(os.getcwd())

def _ensure_safe_path(path: str) -> str:
    """安全检查：确保目标路径在工作目录内，防止目录穿越"""
    # 将输入路径转为基于 WORKSPACE_DIR 的绝对路径
    abs_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not abs_path.startswith(WORKSPACE_DIR):
        raise PermissionError(f"安全限制：禁止访问工作目录之外的路径 ({path})")
    return abs_path

def list_files(path: str = ".") -> str:
    """列出指定目录下的所有文件和文件夹"""
    try:
        safe_path = _ensure_safe_path(path)
        if not os.path.exists(safe_path):
            raise AgentError(
                code="E_FILE_NOT_FOUND",
                type="FileError",
                message=f"路径 {path} 不存在。",
                details=f"The path '{safe_path}' does not exist.",
                retryable=False,
                suggested_actions=["Verify the file path.", "List files in the directory to check if the file exists."]
            )
        if not os.path.isdir(safe_path):
            raise AgentError(
                code="E_FILE_NOT_FOUND",
                type="FileError",
                message=f"{path} 不是一个目录。",
                details=f"The path '{safe_path}' is not a directory.",
                retryable=False,
                suggested_actions=["Verify the file path."]
            )
        
        items = os.listdir(safe_path)
        return "\n".join(items) if items else "目录为空"
    except PermissionError as e:
        raise AgentError(
            code="E_FILE_PERMISSION",
            type="FileError",
            message=str(e),
            retryable=False,
            suggested_actions=["Check file permissions."]
        )
    except Exception as e:
        raise AgentError(
            code="E_INTERNAL",
            type="FileError",
            message=f"读取目录失败: {e}",
            details=str(e),
            retryable=False,
            suggested_actions=["Inspect the agent's logs."]
        )

def read_file(path: str) -> str:
    """读取指定文件内容"""
    try:
        safe_path = _ensure_safe_path(path)
        if not os.path.exists(safe_path):
            raise AgentError(
                code="E_FILE_NOT_FOUND",
                type="FileError",
                message=f"文件 {path} 不存在。",
                details=f"The file '{safe_path}' does not exist.",
                retryable=False,
                suggested_actions=["Verify the file path.", "List files in the directory to check if the file exists."]
            )
        if not os.path.isfile(safe_path):
            raise AgentError(
                code="E_FILE_NOT_FOUND",
                type="FileError",
                message=f"{path} 不是一个文件。",
                details=f"The path '{safe_path}' is not a file.",
                retryable=False,
                suggested_actions=["Verify the file path."]
            )
            
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 防止输出过长撑爆上下文
            if len(content) > 10000:
                return content[:10000] + "\n...[内容过长已截断]..."
            return content
    except PermissionError as e:
        raise AgentError(
            code="E_FILE_PERMISSION",
            type="FileError",
            message=str(e),
            retryable=False,
            suggested_actions=["Check file permissions."]
        )
    except Exception as e:
        raise AgentError(
            code="E_INTERNAL",
            type="FileError",
            message=f"读取文件失败: {e}",
            details=str(e),
            retryable=False,
            suggested_actions=["Inspect the agent's logs."]
        )

def write_file(path: str, content: str) -> str:
    """创建或覆盖指定文件"""
    try:
        safe_path = _ensure_safe_path(path)
        # 确保所在目录存在
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功写入文件: {path}"
    except PermissionError as e:
        raise AgentError(
            code="E_FILE_PERMISSION",
            type="FileError",
            message=str(e),
            retryable=False,
            suggested_actions=["Check file permissions."]
        )
    except Exception as e:
        raise AgentError(
            code="E_FILE_WRITE",
            type="FileError",
            message=f"写入文件失败: {e}",
            details=str(e),
            retryable=True,
            suggested_actions=["Retry writing to the file."]
        )

def edit_file(path: str, old_str: str, new_str: str) -> str:
    """修改文件内容：通过字符串精确查找替换"""
    try:
        safe_path = _ensure_safe_path(path)
        if not os.path.exists(safe_path):
            raise AgentError(
                code="E_FILE_NOT_FOUND",
                type="FileError",
                message=f"文件 {path} 不存在。",
                details=f"The file '{safe_path}' does not exist.",
                retryable=False,
                suggested_actions=["Verify the file path.", "List files in the directory to check if the file exists."]
            )
            
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_str not in content:
            raise AgentError(
                code="E_FILE_WRITE",
                type="FileError",
                message=f"在文件 {path} 中未找到指定的旧字符串。请检查是否完全匹配。",
                retryable=False
            )
            
        # 只替换第一次出现的，防止意外替换多处
        new_content = content.replace(old_str, new_str, 1)
        
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"成功修改文件: {path}"
    except PermissionError as e:
        raise AgentError(
            code="E_FILE_PERMISSION",
            type="FileError",
            message=str(e),
            retryable=False,
            suggested_actions=["Check file permissions."]
        )
    except Exception as e:
        raise AgentError(
            code="E_FILE_WRITE",
            type="FileError",
            message=f"修改文件失败: {e}",
            details=str(e),
            retryable=True,
            suggested_actions=["Retry writing to the file."]
        )

def search_files(query: str, path: str = ".") -> str:
    """在工作目录下简单搜索包含指定字符串的文件"""
    safe_path = _ensure_safe_path(path)
    results = []
    
    # 简单遍历所有文件
    for root, dirs, files in os.walk(safe_path):
        # 排除隐藏目录和常用缓存目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if query in line:
                            rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
                            results.append(f"{rel_path}:{i+1}: {line.strip()}")
            except:
                pass # 忽略不可读的文件(如二进制)
                
    if not results:
        return f"未找到包含 '{query}' 的内容。"
    
    out = "\n".join(results)
    if len(out) > 5000:
        return out[:5000] + "\n...[结果过多已截断]..."
    return out