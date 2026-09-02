from typing import Dict, List, Optional
from coding_agent.skills.base import BaseSkill

class SkillRegistry:
    """
    Skill registry, responsible for managing all available skill instances.
    """
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        """Register a new skill."""
        if skill.name in self._skills:
            # Optionally, handle updates or raise an error
            print(f"Warning: Skill '{skill.name}' is already registered. Overwriting.")
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill instance by name."""
        return self._skills.get(name)

    def get_all_skills(self) -> List[BaseSkill]:
        """Get all registered skills."""
        return list(self._skills.values())

    def get_skill_schemas(self) -> List[Dict]:
        """Get the schemas of all registered skills."""
        return [skill.to_dict() for skill in self.get_all_skills()]

# Global instance of the skill registry
skill_registry = SkillRegistry()

def register_skill(skill: BaseSkill):
    """Decorator to register a skill."""
    skill_registry.register(skill)
    return skill
