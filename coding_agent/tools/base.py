from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """
    所有工具的基类。
    定义了工具的标准接口：名称、描述、参数模式、验证逻辑和执行逻辑。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能描述"""
        pass

    @property
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """输入参数的 JSON Schema 定义"""
        pass

    @property
    def parallel_safe(self) -> bool:
        """工具是否可以并行执行"""
        return False

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行工具的具体逻辑"""
        pass

    def validate(self, **kwargs) -> bool:
        """
        验证参数合法性。默认实现可以根据 input_schema 进行基础检查。
        子类可以覆盖此方法以实现更复杂的业务校验。
        """
        # 这里可以集成 jsonschema 校验，或者简单的必填项检查
        required_fields = self.input_schema.get("required", [])
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"缺失必填参数: {field}")
        return True

    def to_openai_tool(self) -> Dict[str, Any]:
        """将工具转换为 OpenAI API 所需的格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }
