import json
import time
import concurrent.futures
from collections import defaultdict
from typing import Optional

from coding_agent.core.model_client import LLMClient
from coding_agent.core.context import Memory
from coding_agent.core.memory import MemoryManager
from coding_agent.tools.registry import registry, api_registry
from coding_agent.core.error import AgentError
from coding_agent.planning.planner import Planner
from coding_agent.tracing.tracer import Tracer
from coding_agent.core.result_analyzer import ResultAnalyzer
from coding_agent.skills.registry import skill_registry
from coding_agent.skills.base import BaseSkill


class Runtime:
    """
    The Agent Runtime is the core execution engine for the agent.
    It orchestrates the agent's lifecycle, including planning, tool execution,
    and interaction with the language model.
    """
    def __init__(self, 
                 llm_client: LLMClient, 
                 memory: Memory, 
                 max_steps: int = 25, 
                 timeout_seconds: int = 300, 
                 planning_mode: bool = False, 
                 react_mode: bool = False, 
                 hybrid_mode: bool = False):
        self.llm = llm_client
        self.memory = memory
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.planning_mode = planning_mode or hybrid_mode
        self.react_mode = react_mode or hybrid_mode
        self.hybrid_mode = hybrid_mode
        self.result_analyzer = ResultAnalyzer()
        self.memory_manager = MemoryManager(llm_client)
        self.active_skill: Optional[BaseSkill] = None
        
        # Anti-loop mechanisms state
        self._tool_call_history = defaultdict(int)
        self._last_tool_calls = None
        self._no_progress_count = 0

        # Trace system
        self.tracer = None

        # Plan-Execute architecture
        if self.planning_mode:
            self.planner = Planner(llm_client)
            self.plan = None

    def _get_available_tools(self):
        if self.active_skill and self.active_skill.allowed_tools:
            allowed_tool_names = self.active_skill.allowed_tools + ['use_skill']
            return [tool.to_openai_tool() for tool in registry.get_all_tools() if tool.name in allowed_tool_names]
        return api_registry.get_all_summaries()

    def _sync_memory(self):
        """Sync mid-term and long-term memory into the context manager."""
        long_term = self.memory_manager.get_long_term_context()
        mid_term = self.memory_manager.get_mid_term_context()
        self.memory.update_memory(long_term=long_term, mid_term=mid_term)

    def _execute_tool(self, tool_call, step_id=None):
        tool_name = tool_call.function.name
        tool_args_str = tool_call.function.arguments

        if tool_name == 'use_skill':
            try:
                args = json.loads(tool_args_str)
                skill_name = args.get('skill_name')
                skill = skill_registry.get_skill(skill_name)
                if skill:
                    self.active_skill = skill
                    result = f"Skill '{skill_name}' is now active. Instructions: {skill.instructions}"
                    self.memory.add_message("system", result)
                    print(f"[System]: {result}")
                    return tool_call.id, result, None
                else:
                    error = AgentError(code="E_SKILL_NOT_FOUND", type="SkillError", message=f"Skill '{skill_name}' not found.")
                    result = json.dumps(error.to_dict(), ensure_ascii=False)
                    return tool_call.id, result, "E_SKILL_NOT_FOUND"
            except Exception as e:
                error = AgentError(code="E_SKILL_ERROR", type="SkillError", message=f"Error activating skill: {e}")
                result = json.dumps(error.to_dict(), ensure_ascii=False)
                return tool_call.id, result, "E_SKILL_ERROR"
        
        print(f"\n[System]: Agent invokes tool -> {tool_name}")
        print(f"[Arguments]: {tool_args_str}")

        if self.tracer:
            try:
                args = json.loads(tool_args_str)
            except:
                args = {"raw": tool_args_str}
            self.tracer.log_tool_call(tool_name, args, step=step_id)

        self._tool_call_history[(tool_name, tool_args_str)] += 1
        
        start_time = time.time()
        error_code = None
        
        tool = registry.get_tool(tool_name)
        if not tool:
            error = AgentError(
                code="E_TOOL_NOT_FOUND",
                type="ToolError",
                message=f"Tool '{tool_name}' does not exist."
            )
            result = json.dumps(error.to_dict(), ensure_ascii=False)
            error_code = "E_TOOL_NOT_FOUND"
        else:
            try:
                args = json.loads(tool_args_str)
                tool.validate(**args)
                result = tool.execute(**args)
            except json.JSONDecodeError:
                error = AgentError(
                    code="E_TOOL_INVALID_ARGS",
                    type="ToolError",
                    message="Tool arguments JSON parsing failed."
                )
                result = json.dumps(error.to_dict(), ensure_ascii=False)
                error_code = "E_TOOL_INVALID_ARGS"
            except AgentError as e:
                result = json.dumps(e.to_dict(), ensure_ascii=False)
                error_code = e.code
            except Exception as e:
                error = AgentError(
                    code="E_INTERNAL",
                    type="AgentError",
                    message=f"An unknown exception occurred while executing the tool: {e}",
                    details=str(e)
                )
                result = json.dumps(error.to_dict(), ensure_ascii=False)
                error_code = "E_INTERNAL"
        
        latency = time.time() - start_time
        if self.tracer:
            raw_result_summary = str(result)[:500] + ("..." if len(str(result)) > 500 else "")
            self.tracer.log_tool_result(tool_name, raw_result_summary, latency, step=step_id, error_code=error_code)

        compressed_result = self.result_analyzer.compress(result, tool_name)

        print(f"[Execution Result]:\n{compressed_result[:500]}{'...' if len(compressed_result)>500 else ''}")
        return tool_call.id, compressed_result, error_code

    def _execute_step(self, step):
        print(f"\n--- [Executing Step {step['id']}: {step['description']}] ---")
        self.memory.add_message("system", f"Now, execute this step: {step['description']}")
        
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            
            mode_name = "ReAct-Step" if self.react_mode else "Execute-Step"
            print(f"\n--- [{mode_name} Iteration {iteration}] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[System Warning]: Step execution reached global timeout ({self.timeout_seconds}s)!")
                return "timeout"
            
            self._sync_memory()
            
            tools = self._get_available_tools()
            
            if self.memory.get_total_tokens() > self.memory.token_budget:
                self.memory.compress()
                if self.tracer:
                    self.tracer.log_event("context_compression", {"tokens_before": self.memory.get_total_tokens()}, step=step["id"])

            try:
                start_time_llm = time.time()
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
                latency_llm = time.time() - start_time_llm
                
                if self.tracer:
                    prompt_summary = f"Messages: {len(self.memory.messages)}"
                    response_summary = response_msg.content[:200] + "..." if response_msg.content and len(response_msg.content) > 200 else (response_msg.content or "Tool Calls")
                    self.tracer.log_model_call(self.llm.model, prompt_summary, response_summary, latency_llm, step=step["id"])

            except Exception as e:
                print(f"[System Error]: LLM request failed: {e}")
                if self.tracer:
                    self.tracer.log_event("model_error", {"error": str(e)}, step=step["id"])
                return "llm_error"
            
            self.memory.add_assistant_message(response_msg)
            
            if response_msg.content:
                print(f"[Agent {'Decision' if self.react_mode else 'Response'}]:\n{response_msg.content}")
                
            if response_msg.tool_calls:
                current_tool_calls_tuple = tuple(sorted((tc.function.name, tc.function.arguments) for tc in response_msg.tool_calls))
                if self._last_tool_calls == current_tool_calls_tuple:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0
                self._last_tool_calls = current_tool_calls_tuple

                if self._no_progress_count >= 3:
                     print("\n[System Warning]: Agent has issued the same tool call 3 times in a row, possibly stuck in a no-progress loop.")
                     self.memory.add_message("system", "You seem to be making no progress. Please choose a different strategy.")
                     if self.tracer:
                         self.tracer.log_event("loop_warning", {"reason": "repeated_tool_calls"}, step=step["id"])
                
                if iteration % 5 == 0:
                    self.memory_manager.extract_insights(self.memory.messages)
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[System Warning]: Tool {call_tuple[0]} with the same arguments has been called 3 times, possibly in a loop!")
                        if self.tracer:
                            self.tracer.log_event("loop_detected", {"tool": call_tuple[0]}, step=step["id"])
                        return "loop_detected"

                parallel_calls = []
                serial_calls = []

                for tool_call in response_msg.tool_calls:
                    tool = registry.get_tool(tool_call.function.name)
                    if tool and tool.parallel_safe:
                        parallel_calls.append(tool_call)
                    else:
                        serial_calls.append(tool_call)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    parallel_results = list(executor.map(lambda tc: self._execute_tool(tc, step_id=step["id"]), parallel_calls))
                    for tool_call_id, result, error_code in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)
                        if error_code in ["E_TOOL_NOT_FOUND", "E_TOOL_INVALID_ARGS"]:
                            tool_name = response_msg.tool_calls[int(tool_call_id.split('_')[-1])].function.name
                            full_schema = api_registry.get_full_schema(tool_name)
                            if full_schema:
                                self.memory.add_message("system", f"Error: Call to tool {tool_name} failed. Here is the full documentation for the tool, please correct your call:\n{json.dumps(full_schema, ensure_ascii=False, indent=2)}")

                for tool_call in serial_calls:
                    tool_call_id, result, error_code = self._execute_tool(tool_call, step_id=step["id"])
                    self.memory.add_tool_message(tool_call_id, result)
                    if error_code in ["E_TOOL_NOT_FOUND", "E_TOOL_INVALID_ARGS"]:
                        tool_name = tool_call.function.name
                        full_schema = api_registry.get_full_schema(tool_name)
                        if full_schema:
                            self.memory.add_message("system", f"Error: Call to tool {tool_name} failed. Here is the full documentation for the tool, please correct your call:\n{json.dumps(full_schema, ensure_ascii=False, indent=2)}")
            else:
                print("\n[System]: Agent believes this step is complete.")
                self.memory_manager.extract_insights(self.memory.messages)
                return "completed"
                
        return "max_steps_reached"


    def run(self, user_input: str):
        """Main Agent Loop"""
        self.tracer = Tracer()
        self.tracer.log_event("task_start", {"user_input": user_input, "mode": self._get_current_mode()})
        
        self.memory.add_message("user", content=user_input)
        print(f"\n[User Task]: {user_input}")
        print("-" * 50)
        
        try:
            if self.planning_mode:
                mode_type = "Plan + ReAct Hybrid Mode" if self.hybrid_mode else "Planning Mode"
                print(f"\n[System]: Entering {mode_type}...")
                self.plan = self.planner.create_plan(user_input)
                
                if not self.plan:
                    print("[System]: Could not create a plan, switching to standard execution mode.")
                    self._run_without_plan(user_input)
                else:
                    self.memory.update_plan(self.plan)
                    self.tracer.log_event("plan_generated", {"plan": self.plan})
                    print("\n[System]: Plan generated, executing step by step...")
                    print(json.dumps(self.plan, indent=2, ensure_ascii=False))
                    print("-" * 50)
                    
                    i = 0
                    while i < len(self.plan["steps"]):
                        step = self.plan["steps"][i]
                        if step["status"] == "completed":
                            i += 1
                            continue

                        step["status"] = "in_progress"
                        status = self._execute_step(step)
                        
                        if status == "completed":
                            step["status"] = "completed"
                            print(f"\n--- [Step {step['id']} Completed] ---")
                            i += 1
                        else:
                            step["status"] = "failed"
                            print(f"\n--- [Step {step['id']} Failed, Status: {status}] ---")
                            
                            if self.hybrid_mode:
                                print("\n[System]: Triggering dynamic plan adjustment in hybrid mode...")
                                self.tracer.log_event("plan_adaptive_trigger", {"step_id": step["id"], "reason": status})
                                new_plan = self.planner.update_plan(user_input, self.plan, self.memory.get_messages())
                                if new_plan:
                                    print("\n[System]: Plan updated!")
                                    print(json.dumps(new_plan, indent=2, ensure_ascii=False))
                                    self.plan = new_plan
                                    self.memory.update_plan(self.plan)
                                    self.tracer.log_event("plan_updated", {"new_plan": self.plan})
                                    # Restart from the first unfinished step
                                    i = 0 
                                    continue
                            
                            print("\n[System]: Agent stopping execution due to step failure and inability to auto-adjust plan.")
                            break 
                    
                    print("\n[System]: Task execution process finished.")

            elif self.react_mode:
                self._run_react_mode(user_input)

            else:
                self._run_without_plan(user_input)
            
            final_response = "Task execution finished"
            if self.memory.messages and self.memory.messages[-1]["role"] == "assistant":
                final_response = self.memory.messages[-1]["content"]
            
            self.tracer.finalize(final_response)
            
        except Exception as e:
            self.tracer.log_event("agent_error", {
                "summary": "An exception occurred during agent execution",
                "error_message": str(e),
                "error_type": type(e).__name__
            })
            raise e

    def _get_current_mode(self) -> str:
        if self.hybrid_mode: return "hybrid"
        if self.planning_mode: return "plan"
        if self.react_mode: return "react"
        return "standard"

    def _run_react_mode(self, user_input: str):
        print("\n[System]: Entering ReAct mode...")
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            print(f"\n--- [ReAct Iteration {iteration}: Reason/Act] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[System Warning]: Agent reached global timeout ({self.timeout_seconds}s) and was forcibly interrupted!")
                break
            
            self._sync_memory()
            
            tools = self._get_available_tools()
            
            if self.memory.get_total_tokens() > self.memory.token_budget:
                self.memory.compress()
                if self.tracer:
                    self.tracer.log_event("context_compression", {"tokens_before": self.memory.get_total_tokens()}, step=iteration)

            try:
                start_time_llm = time.time()
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
                latency_llm = time.time() - start_time_llm
                
                if self.tracer:
                    prompt_summary = f"Messages: {len(self.memory.messages)}"
                    response_summary = response_msg.content[:200] + "..." if response_msg.content and len(response_msg.content) > 200 else (response_msg.content or "Tool Calls")
                    self.tracer.log_model_call(self.llm.model, prompt_summary, response_summary, latency_llm, step=iteration)

            except Exception as e:
                print(f"[System Error]: LLM request failed: {e}")
                if self.tracer:
                    self.tracer.log_event("model_error", {"error": str(e)}, step=iteration)
                break
            
            self.memory.add_assistant_message(response_msg)
            
            if response_msg.content:
                print(f"[Agent Decision]:\n{response_msg.content}")
                
            if response_msg.tool_calls:
                current_tool_calls_tuple = tuple(sorted((tc.function.name, tc.function.arguments) for tc in response_msg.tool_calls))
                if self._last_tool_calls == current_tool_calls_tuple:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0
                self._last_tool_calls = current_tool_calls_tuple

                if self._no_progress_count >= 3:
                     print("\n[System Warning]: Agent has issued the same tool call 3 times in a row, possibly stuck in a no-progress loop.")
                     self.memory.add_message("system", "You seem to be making no progress. Please choose a different strategy.")
                     if self.tracer:
                         self.tracer.log_event("loop_warning", {"reason": "repeated_tool_calls"}, step=iteration)
                
                if iteration % 5 == 0:
                    self.memory_manager.extract_insights(self.memory.messages)
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[System Warning]: Tool {call_tuple[0]} with the same arguments has been called 3 times, possibly in a loop, interrupting execution!")
                        if self.tracer:
                            self.tracer.log_event("loop_detected", {"tool": call_tuple[0]}, step=iteration)
                        iteration = self.max_steps 
                        break
                if iteration >= self.max_steps:
                    break
                
                parallel_calls = []
                serial_calls = []

                for tool_call in response_msg.tool_calls:
                    tool = registry.get_tool(tool_call.function.name)
                    if tool and tool.parallel_safe:
                        parallel_calls.append(tool_call)
                    else:
                        serial_calls.append(tool_call)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    parallel_results = list(executor.map(lambda tc: self._execute_tool(tc, step_id=iteration), parallel_calls))
                    for tool_call_id, result, error_code in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)
                        if error_code in ["E_TOOL_NOT_FOUND", "E_TOOL_INVALID_ARGS"]:
                            tool_name = response_msg.tool_calls[int(tool_call_id.split('_')[-1])].function.name
                            full_schema = api_registry.get_full_schema(tool_name)
                            if full_schema:
                                self.memory.add_message("system", f"Error: Call to tool {tool_name} failed. Here is the full documentation for the tool, please correct your call:\n{json.dumps(full_schema, ensure_ascii=False, indent=2)}")

                for tool_call in serial_calls:
                    tool_call_id, result, error_code = self._execute_tool(tool_call, step_id=iteration)
                    self.memory.add_tool_message(tool_call_id, result)
                    if error_code in ["E_TOOL_NOT_FOUND", "E_TOOL_INVALID_ARGS"]:
                        tool_name = tool_call.function.name
                        full_schema = api_registry.get_full_schema(tool_name)
                        if full_schema:
                            self.memory.add_message("system", f"Error: Call to tool {tool_name} failed. Here is the full documentation for the tool, please correct your call:\n{json.dumps(full_schema, ensure_ascii=False, indent=2)}")
            else:
                print("\n[System]: Agent believes the task is complete, loop ends.")
                if response_msg.content:
                    print(f"\n[Agent Final Response]:\n{response_msg.content}")
                
                self.memory_manager.extract_insights(self.memory.messages)
                break
                
        if iteration >= self.max_steps:
            print(f"\n[System Warning]: Agent reached the maximum thinking iteration limit ({self.max_steps} steps) and was forcibly interrupted by the safety mechanism!")

    def _run_without_plan(self, user_input: str):
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            print(f"\n--- [Agent Thinking Iteration {iteration}] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[System Warning]: Agent reached global timeout ({self.timeout_seconds}s) and was forcibly interrupted by the safety mechanism!")
                break
            
            self._sync_memory()
            
            tools = self._get_available_tools()
            
            if self.memory.get_total_tokens() > self.memory.token_budget:
                self.memory.compress()
                if self.tracer:
                    self.tracer.log_event("context_compression", {"tokens_before": self.memory.get_total_tokens()}, step=iteration)

            try:
                start_time_llm = time.time()
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
                latency_llm = time.time() - start_time_llm
                
                if self.tracer:
                    prompt_summary = f"Messages: {len(self.memory.messages)}"
                    response_summary = response_msg.content[:200] + "..." if response_msg.content and len(response_msg.content) > 200 else (response_msg.content or "Tool Calls")
                    self.tracer.log_model_call(self.llm.model, prompt_summary, response_summary, latency_llm, step=iteration)

            except Exception as e:
                print(f"[System Error]: LLM request failed: {e}")
                if self.tracer:
                    self.tracer.log_event("model_error", {"error": str(e)}, step=iteration)
                break
            
            self.memory.add_assistant_message(response_msg)
            
            if response_msg.content:
                print(f"[Agent Response]:\n{response_msg.content}")
                
            if response_msg.tool_calls:
                current_tool_calls_tuple = tuple(sorted((tc.function.name, tc.function.arguments) for tc in response_msg.tool_calls))
                if self._last_tool_calls == current_tool_calls_tuple:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0
                self._last_tool_calls = current_tool_calls_tuple

                if self._no_progress_count >= 3:
                     print("\n[System Warning]: Agent has issued the same tool call 3 times in a row, possibly stuck in a no-progress loop.")
                     self.memory.add_message("system", "You seem to be making no progress. Please choose a different strategy.")
                     if self.tracer:
                         self.tracer.log_event("loop_warning", {"reason": "repeated_tool_calls"}, step=iteration)

                if iteration % 5 == 0:
                    self.memory_manager.extract_insights(self.memory.messages)
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[System Warning]: Tool {call_tuple[0]} with the same arguments has been called 3 times, possibly in a loop, interrupting execution!")
                        if self.tracer:
                            self.tracer.log_event("loop_detected", {"tool": call_tuple[0]}, step=iteration)
                        iteration = self.max_steps 
                        break
                if iteration >= self.max_steps:
                    break
                
                parallel_calls = []
                serial_calls = []

                for tool_call in response_msg.tool_calls:
                    tool = registry.get_tool(tool_call.function.name)
                    if tool and tool.parallel_safe:
                        parallel_calls.append(tool_call)
                    else:
                        serial_calls.append(tool_call)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    parallel_results = list(executor.map(lambda tc: self._execute_tool(tc, step_id=iteration), parallel_calls))
                    for tool_call_id, result, error_code in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)
                        if error_code in ["E_TOOL_NOT_FOUND", "E_TOOL_INVALID_ARGS"]:
                            tool_name = response_msg.tool_calls[int(tool_call_id.split('_')[-1])].function.name
                            full_schema = api_registry.get_full_schema(tool_name)
                            if full_schema:
                                self.memory.add_message("system", f"Error: Call to tool {tool_name} failed. Here is the full documentation for the tool, please correct your call:\n{json.dumps(full_schema, ensure_ascii=False, indent=2)}")

                for tool_call in serial_calls:
                    tool_call_id, result, error_code = self._execute_tool(tool_call, step_id=iteration)
                    self.memory.add_tool_message(tool_call_id, result)
                    if error_code in ["E_TOOL_NOT_FOUND", "E_TOOL_INVALID_ARGS"]:
                        tool_name = tool_call.function.name
                        full_schema = api_registry.get_full_schema(tool_name)
                        if full_schema:
                            self.memory.add_message("system", f"Error: Call to tool {tool_name} failed. Here is the full documentation for the tool, please correct your call:\n{json.dumps(full_schema, ensure_ascii=False, indent=2)}")
            else:
                print("\n[System]: Agent believes the task is complete, loop ends.")
                self.memory_manager.extract_insights(self.memory.messages)
                break
                
        if iteration >= self.max_steps:
            print(f"\n[System Warning]: Agent reached the maximum thinking iteration limit ({self.max_steps} steps) and was forcibly interrupted by the safety mechanism!")
