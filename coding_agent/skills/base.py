from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseSkill(ABC):
    """
    Base class for all skills.
    Defines the standard interface for a skill.
    A skill is a combination of tools, prompts, and a workflow to accomplish a more complex task.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the skill."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the skill does."""
        pass
        
    @property
    @abstractmethod
    def when_to_use(self) -> str:
        """Describes when to use this skill."""
        pass

    @property
    @abstractmethod
    def instructions(self) -> str:
        """Instructions for the model on how to use the skill."""
        pass

    @property
    def allowed_tools(self) -> List[str]:
        """A list of tool names that this skill is allowed to use."""
        return []

    @property
    def workflow(self) -> List[Dict[str, Any]]:
        """The workflow of the skill, a list of steps."""
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the skill."""
        return {
            "name": self.name,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "instructions": self.instructions,
            "allowed_tools": self.allowed_tools,
            "workflow": self.workflow,
        }
