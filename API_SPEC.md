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
```

## ResultAnalyzer 接口

```python
class ResultAnalyzer:
    def __init__(self, max_output_tokens: int = 1024): ...
    def compress(self, tool_output: any, tool_name: str) -> str: ...
    def _truncate_text(self, text: str, max_len: int) -> str: ...
```

## BaseSkill 接口

```python
class BaseSkill(ABC):
    name: str # 技能名称
    description: str # 技能描述
    when_to_use: str # 何时使用该技能
    instructions: str # 给模型的技能使用说明
    allowed_tools: List[str] # 技能允许使用的工具列表
    workflow: List[Dict[str, Any]] # 技能的工作流步骤
    
    def to_dict(self) -> Dict[str, Any]: ...
```

## SkillRegistry 接口

```python
class SkillRegistry:
    def register(self, skill: BaseSkill): ...
    def get_skill(self, name: str) -> Optional[BaseSkill]: ...
    def get_all_skills(self) -> List[BaseSkill]: ...
    def get_skill_schemas(self) -> List[Dict]: ...
```
