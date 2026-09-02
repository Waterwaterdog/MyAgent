from typing import Any, Dict, List
from coding_agent.skills.base import BaseSkill
from coding_agent.skills.registry import register_skill

@register_skill
class DebuggingSkill(BaseSkill):
    """
    A skill for debugging code. It follows a structured workflow to identify and fix errors.
    """

    @property
    def name(self) -> str:
        return "debugging"

    @property
    def description(self) -> str:
        return "Skill to debug and fix errors in the codebase."

    @property
    def when_to_use(self) -> str:
        return "When you encounter a bug, a test failure, or an error that you need to fix."

    @property
    def instructions(self) -> str:
        return (
            "Follow the debugging workflow step-by-step. "
            "Use the available tools to inspect the code, reproduce the error, "
            "find the root cause, apply a patch, and verify the fix."
        )

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "list_files",
            "read_file",
            "write_file",
            "edit_file",
            "run_command",
            "search_files",
        ]

    @property
    def workflow(self) -> List[Dict[str, Any]]:
        return [
            {"step": 1, "description": "Inspect the project structure to understand the layout."},
            {"step": 2, "description": "Try to reproduce the error to confirm its existence."},
            {"step": 3, "description": "Inspect relevant logs and code to find the root cause."},
            {"step": 4, "description": "Identify the root cause of the error."},
            {"step": 5, "description": "Apply a patch to fix the code."},
            {"step": 6, "description": "Run regression tests to verify the fix and ensure no new issues are introduced."},
        ]
