import os
from typing import Any, Dict
from coding_agent.tools.base import BaseTool
from coding_agent.tools.file_ops import list_files, read_file, write_file, edit_file, search_files

class ListFilesTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "列出指定目录下的所有文件和文件夹"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要列出的相对目录路径，例如 '.'"}
            },
            "required": ["path"]
        }

    @property
    def parallel_safe(self) -> bool:
        return True

    def execute(self, **kwargs) -> str:
        return list_files(kwargs.get("path", "."))

class ReadFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取指定文件的内容"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"}
            },
            "required": ["path"]
        }

    @property
    def parallel_safe(self) -> bool:
        return True

    def execute(self, **kwargs) -> str:
        return read_file(kwargs.get("path"))

class WriteFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "创建或完全覆盖文件内容"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的文件完整内容"}
            },
            "required": ["path", "content"]
        }

    def execute(self, **kwargs) -> str:
        return write_file(kwargs.get("path"), kwargs.get("content"))

class EditFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "修改文件内容（通过精确查找并替换字符串）"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "old_str": {"type": "string", "description": "要替换的旧字符串（必须与文件内完全一致）"},
                "new_str": {"type": "string", "description": "新的字符串"}
            },
            "required": ["path", "old_str", "new_str"]
        }

    def execute(self, **kwargs) -> str:
        return edit_file(kwargs.get("path"), kwargs.get("old_str"), kwargs.get("new_str"))

class SearchFilesTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return "在目录中搜索包含指定字符串的文件"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "要搜索的文本"},
                "path": {"type": "string", "description": "要搜索的相对目录路径，默认 '.'"}
            },
            "required": ["query"]
        }

    @property
    def parallel_safe(self) -> bool:
        return True

    def execute(self, **kwargs) -> str:
        return search_files(kwargs.get("query"), kwargs.get("path", "."))
