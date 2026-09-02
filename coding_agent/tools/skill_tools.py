from coding_agent.tools.base import BaseTool
from coding_agent.skills.registry import skill_registry

class UseSkillTool(BaseTool):
    """
    A tool to activate a specific skill. When a skill is activated, 
    the agent's context is updated with the skill's instructions and 
    its allowed tools are prioritized.
    """
    @property
    def name(self) -> str:
        return "use_skill"

    @property
    def description(self) -> str:
        return "Activates a skill to handle a complex task. Use this when a user's request matches a skill's purpose."

    @property
    def input_schema(self) -> dict:
        skills = skill_registry.get_all_skills()
        skill_names = [skill.name for skill in skills] if skills else []
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill to use.",
                    "enum": skill_names,
                }
            },
            "required": ["skill_name"],
        }
    
    def execute(self, skill_name: str) -> str:
        skill = skill_registry.get_skill(skill_name)
        if not skill:
            return f"Error: Skill '{skill_name}' not found."
        
        # The actual skill activation logic will be handled by the agent loop
        # This tool's purpose is to signal the intent to use a skill.
        return f"Skill '{skill_name}' activated. The agent will now follow the skill's workflow and instructions."
