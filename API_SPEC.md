# API Specification

This document will define the API specifications for tools and other components.

## BaseTool 接口

```python
class BaseTool(ABC):
    name: str # 工具名称
    description: str # 工具功能描述
    input_schema: Dict[str, Any] # 输入参数的 JSON Schema 定义
    parallel_safe: bool # 工具是否可以并行执行
    
    def execute(self, **kwargs) -> str: ...
    def validate(self, **kwargs) -> bool: ...
    def to_openai_tool(self) -> Dict[str, Any]: ...
```

## ToolRegistry 接口

```python
class ToolRegistry:
    def register(self, tool: BaseTool): ...
    def get_tool(self, name: str) -> Optional[BaseTool]: ...
    def get_all_tools(self) -> List[BaseTool]: ...
    def get_openai_schemas(self) -> List[Dict[str, Any]]: ...
27→```
28→
29→## ResultAnalyzer 接口
30→
31→```python
32→class ResultAnalyzer:
33→    def __init__(self, max_output_tokens: int = 1024): ...
34→    def compress(self, tool_output: any, tool_name: str) -> str: ...
35→    def _truncate_text(self, text: str, max_len: int) -> str: ...
36→```
```
