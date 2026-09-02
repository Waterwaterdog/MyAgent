from coding_agent.core.model_client import LLMClient
from coding_agent.core.context import Memory
from coding_agent.runtime.runtime import Runtime

class Agent:
    """
    The Agent is the main container for the coding agent.
    It is responsible for initializing all the necessary components and
    running the agent's lifecycle.
    """
    def __init__(self, llm_client: LLMClient, memory: Memory, max_steps: int = 25, timeout_seconds: int = 300, 
                 planning_mode: bool = False, react_mode: bool = False, hybrid_mode: bool = False):
        
        self.runtime = Runtime(
            llm_client=llm_client,
            memory=memory,
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
            planning_mode=planning_mode,
            react_mode=react_mode,
            hybrid_mode=hybrid_mode
        )

    def run(self, user_input: str):
        """Run the agent with the given user input."""
        self.runtime.run(user_input)
