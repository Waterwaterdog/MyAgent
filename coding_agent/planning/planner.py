import json
from coding_agent.core.model_client import LLMClient
from coding_agent.core.context import Memory

PLANNER_SYSTEM_PROMPT = """
You are a master planner. Your task is to break down a complex user request into a series of simple, executable steps.
The plan should be as a JSON object with a "goal" and a list of "steps".
Each step should have an "id", a "description", and a "status" which is initially "pending".
The steps should be logical and sequential.

Example user request: "Create a python file 'app.py' that prints 'hello world', and then run it."

Example plan:
{
  "goal": "Create a python file 'app.py' that prints 'hello world', and then run it.",
  "steps": [
    {
      "id": 1,
      "description": "Create a new file named 'app.py' with the content 'print(\"hello world\")'",
      "status": "pending"
    },
    {
      "id": 2,
      "description": "Execute the python file 'app.py'",
      "status": "pending"
    }
  ]
}
"""

class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def create_plan(self, user_input: str):
        memory = Memory()
        memory.add_message("system", PLANNER_SYSTEM_PROMPT)
        memory.add_message("user", user_input)
        
        response_msg = self.llm.chat(memory.get_messages())
        
        try:
            # The response may be in a code block
            if "```json" in response_msg.content:
                plan_str = response_msg.content.split("```json")[1].split("```")[0].strip()
            else:
                plan_str = response_msg.content

            plan_json = json.loads(plan_str)
            # Basic validation
            if "goal" in plan_json and "steps" in plan_json:
                # Initialize status
                for step in plan_json["steps"]:
                    step["status"] = "pending"
                return plan_json
            else:
                raise ValueError("Invalid plan structure: 'goal' or 'steps' is missing.")
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            # Here we could have a retry mechanism or a more robust error handling
            print(f"[Planner]: Failed to create a valid plan. Error: {e}, Content: {response_msg.content}")
            return None

