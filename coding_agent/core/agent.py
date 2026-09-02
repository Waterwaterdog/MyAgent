import json
import time
import concurrent.futures
from collections import defaultdict
from coding_agent.core.model_client import LLMClient
from coding_agent.core.context import Memory
from coding_agent.tools.registry import registry
from coding_agent.core.error import AgentError
from coding_agent.planning.planner import Planner
from coding_agent.tracing.tracer import Tracer

class Agent:
    """
    Agent 主循环控制器。
    负责接收任务、管理循环迭代、请求 LLM、分发工具调用并返回最终结果。
    """
    def __init__(self, llm_client: LLMClient, memory: Memory, max_steps: int = 25, timeout_seconds: int = 300, 
                 planning_mode: bool = False, react_mode: bool = False, hybrid_mode: bool = False):
        self.llm = llm_client
        self.memory = memory
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.planning_mode = planning_mode or hybrid_mode
        self.react_mode = react_mode or hybrid_mode
        self.hybrid_mode = hybrid_mode
        
        # 防死循环机制所需的状态追踪
        self._tool_call_history = defaultdict(int)
        self._last_tool_calls = None
        self._no_progress_count = 0

        # Trace 系统
        self.tracer = None

        # Plan-Execute 架构
        if self.planning_mode:
            self.planner = Planner(llm_client)
            self.plan = None

    def _execute_tool(self, tool_call, step_id=None):
        tool_name = tool_call.function.name
        tool_args_str = tool_call.function.arguments
        
        print(f"\n[系统]: Agent 发起工具调用 -> {tool_name}")
        print(f"[参数]: {tool_args_str}")

        # 记录 Trace
        if self.tracer:
            try:
                args = json.loads(tool_args_str)
            except:
                args = {"raw": tool_args_str}
            self.tracer.log_tool_call(tool_name, args, step=step_id)

        # 记录工具调用历史 (用于防死循环)
        self._tool_call_history[(tool_name, tool_args_str)] += 1
        
        start_time = time.time()
        error_code = None
        
        tool = registry.get_tool(tool_name)
        if not tool:
            error = AgentError(
                code="E_TOOL_NOT_FOUND",
                type="ToolError",
                message=f"工具 '{tool_name}' 不存在。"
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
                    message="工具参数 JSON 解析失败。"
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
                    message=f"执行工具时发生未知异常: {e}",
                    details=str(e)
                )
                result = json.dumps(error.to_dict(), ensure_ascii=False)
                error_code = "E_INTERNAL"
        
        latency = time.time() - start_time
        if self.tracer:
            summary = result[:200] + "..." if len(result) > 200 else result
            self.tracer.log_tool_result(tool_name, summary, latency, step=step_id, error_code=error_code)

        print(f"[执行结果]:\n{result[:500]}{'...' if len(result)>500 else ''}")
        return tool_call.id, result

    def _execute_step(self, step):
        print(f"\n--- [执行步骤 {step['id']}: {step['description']}] ---")
        self.memory.add_message("system", f"Now, execute this step: {step['description']}")
        
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            
            # Hybrid 模式下，如果开启了 ReAct，则每一步的执行逻辑也是 ReAct 风格
            mode_name = "ReAct-Step" if self.react_mode else "Execute-Step"
            print(f"\n--- [{mode_name} 轮次 {iteration}] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[系统警告]: 步骤执行达到全局超时限制 ({self.timeout_seconds}秒)！")
                return "timeout"
            
            tools = registry.get_openai_schemas()
            
            try:
                start_time_llm = time.time()
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
                latency_llm = time.time() - start_time_llm
                
                if self.tracer:
                    prompt_summary = f"Messages: {len(self.memory.messages)}"
                    response_summary = response_msg.content[:200] + "..." if response_msg.content and len(response_msg.content) > 200 else (response_msg.content or "Tool Calls")
                    self.tracer.log_model_call(self.llm.model, prompt_summary, response_summary, latency_llm, step=step["id"])

            except Exception as e:
                print(f"[系统错误]: 请求 LLM 失败: {e}")
                if self.tracer:
                    self.tracer.log_event("model_error", {"error": str(e)}, step=step["id"])
                return "llm_error"
            
            self.memory.add_assistant_message(response_msg)
            
            if response_msg.content:
                print(f"[Agent {'决策' if self.react_mode else '回复'}]:\n{response_msg.content}")
                
            if response_msg.tool_calls:
                # Anti-loop mechanisms
                current_tool_calls_tuple = tuple(sorted((tc.function.name, tc.function.arguments) for tc in response_msg.tool_calls))
                if self._last_tool_calls == current_tool_calls_tuple:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0
                self._last_tool_calls = current_tool_calls_tuple

                if self._no_progress_count >= 3:
                     print("\n[系统警告]: Agent 已连续 3 次发起相同的工具调用，可能陷入了无进展循环。")
                     self.memory.add_message("system", "You seem to be making no progress. Please choose a different strategy.")
                     if self.tracer:
                         self.tracer.log_event("loop_warning", {"reason": "repeated_tool_calls"}, step=step["id"])
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[系统警告]: 工具 {call_tuple[0]} 带相同参数已连续调用 3 次，可能陷入死循环！")
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
                    # 并行执行时传入 step_id
                    parallel_results = list(executor.map(lambda tc: self._execute_tool(tc, step_id=step["id"]), parallel_calls))
                    for tool_call_id, result in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)

                for tool_call in serial_calls:
                    tool_call_id, result = self._execute_tool(tool_call, step_id=step["id"])
                    self.memory.add_tool_message(tool_call_id, result)
            else:
                print("\n[系统]: Agent 认为该步骤已完成。")
                return "completed"
                
        return "max_steps_reached"


    def run(self, user_input: str):
        """Agent 主循环 (Agent Loop)"""
        self.tracer = Tracer()
        self.tracer.log_event("task_start", {"user_input": user_input, "mode": self._get_current_mode()})
        
        self.memory.add_message("user", content=user_input)
        print(f"\n[用户任务]: {user_input}")
        print("-" * 50)
        
        try:
            if self.planning_mode:
                mode_type = "Plan + ReAct 混合模式" if self.hybrid_mode else "规划模式"
                print(f"\n[系统]: 进入 {mode_type}...")
                self.plan = self.planner.create_plan(user_input)
                
                if not self.plan:
                    print("[系统]: 无法创建计划，转为标准执行模式。")
                    self._run_without_plan(user_input)
                else:
                    self.tracer.log_event("plan_generated", {"plan": self.plan})
                    print("\n[系统]: 已生成计划，开始按步骤执行...")
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
                            print(f"\n--- [步骤 {step['id']} 完成] ---")
                            i += 1
                        else:
                            step["status"] = "failed"
                            print(f"\n--- [步骤 {step['id']} 失败，状态: {status}] ---")
                            
                            if self.hybrid_mode:
                                print("\n[系统]: 触发混合模式下的计划动态调整...")
                                self.tracer.log_event("plan_adaptive_trigger", {"step_id": step["id"], "reason": status})
                                new_plan = self.planner.update_plan(user_input, self.plan, self.memory.get_messages())
                                if new_plan:
                                    print("\n[系统]: 计划已更新！")
                                    print(json.dumps(new_plan, indent=2, ensure_ascii=False))
                                    self.plan = new_plan
                                    self.tracer.log_event("plan_updated", {"new_plan": self.plan})
                                    # 重新从第一个未完成的步骤开始
                                    i = 0 
                                    continue
                            
                            print("\n[系统]: 由于步骤失败且无法自动调整计划，Agent 停止执行。")
                            break 
                    
                    print("\n[系统]: 任务执行流程结束。")

            elif self.react_mode:
                self._run_react_mode(user_input)

            else:
                self._run_without_plan(user_input)
            
            final_response = "任务执行结束"
            if self.memory.messages and self.memory.messages[-1]["role"] == "assistant":
                final_response = self.memory.messages[-1]["content"]
            
            self.tracer.finalize(final_response)
            
        except Exception as e:
            self.tracer.log_event("agent_error", {
                "summary": "Agent 运行发生异常",
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
        print("\n[系统]: 进入 ReAct 模式...")
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            # The "Observe" part of ReAct is the tool results from the previous step, which are already in memory.
            print(f"\n--- [ReAct 轮次 {iteration}: Reason/Act] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[系统警告]: Agent 达到全局超时限制 ({self.timeout_seconds}秒)，被安全机制强制中断！")
                break
            
            tools = registry.get_openai_schemas()
            
            try:
                start_time_llm = time.time()
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
                latency_llm = time.time() - start_time_llm
                
                if self.tracer:
                    prompt_summary = f"Messages: {len(self.memory.messages)}"
                    response_summary = response_msg.content[:200] + "..." if response_msg.content and len(response_msg.content) > 200 else (response_msg.content or "Tool Calls")
                    self.tracer.log_model_call(self.llm.model, prompt_summary, response_summary, latency_llm, step=iteration)

            except Exception as e:
                print(f"[系统错误]: 请求 LLM 失败: {e}")
                if self.tracer:
                    self.tracer.log_event("model_error", {"error": str(e)}, step=iteration)
                break
            
            self.memory.add_assistant_message(response_msg)
            
            if response_msg.content:
                # This is the "Reason" part
                print(f"[Agent 决策]:\n{response_msg.content}")
                
            if response_msg.tool_calls:
                # This is the "Act" part
                # Anti-loop mechanisms
                current_tool_calls_tuple = tuple(sorted((tc.function.name, tc.function.arguments) for tc in response_msg.tool_calls))
                if self._last_tool_calls == current_tool_calls_tuple:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0
                self._last_tool_calls = current_tool_calls_tuple

                if self._no_progress_count >= 3:
                     print("\n[系统警告]: Agent 已连续 3 次发起相同的工具调用，可能陷入了无进展循环。")
                     self.memory.add_message("system", "You seem to be making no progress. Please choose a different strategy.")
                     if self.tracer:
                         self.tracer.log_event("loop_warning", {"reason": "repeated_tool_calls"}, step=iteration)
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[系统警告]: 工具 {call_tuple[0]} 带相同参数已连续调用 3 次，可能陷入死循环，中断执行！")
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
                
                # The results of these executions are the "Observation"
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    parallel_results = list(executor.map(lambda tc: self._execute_tool(tc, step_id=iteration), parallel_calls))
                    for tool_call_id, result in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)

                for tool_call in serial_calls:
                    tool_call_id, result = self._execute_tool(tool_call, step_id=iteration)
                    self.memory.add_tool_message(tool_call_id, result)
            else:
                print("\n[系统]: Agent 认为任务已完成，循环结束。")
                if response_msg.content:
                    # Final answer
                    print(f"\n[Agent 最终回复]:\n{response_msg.content}")
                break
                
        if iteration >= self.max_steps:
            print(f"\n[系统警告]: Agent 达到最大思考轮次限制 ({self.max_steps}步)，被安全机制强制中断！")

    def _run_without_plan(self, user_input: str):
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            print(f"\n--- [Agent 思考轮次 {iteration}] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[系统警告]: Agent 达到全局超时限制 ({self.timeout_seconds}秒)，被安全机制强制中断！")
                break
            
            tools = registry.get_openai_schemas()
            
            try:
                start_time_llm = time.time()
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
                latency_llm = time.time() - start_time_llm
                
                if self.tracer:
                    prompt_summary = f"Messages: {len(self.memory.messages)}"
                    response_summary = response_msg.content[:200] + "..." if response_msg.content and len(response_msg.content) > 200 else (response_msg.content or "Tool Calls")
                    self.tracer.log_model_call(self.llm.model, prompt_summary, response_summary, latency_llm, step=iteration)

            except Exception as e:
                print(f"[系统错误]: 请求 LLM 失败: {e}")
                if self.tracer:
                    self.tracer.log_event("model_error", {"error": str(e)}, step=iteration)
                break
            
            self.memory.add_assistant_message(response_msg)
            
            if response_msg.content:
                print(f"[Agent 回复]:\n{response_msg.content}")
                
            if response_msg.tool_calls:
                # Anti-loop mechanisms
                current_tool_calls_tuple = tuple(sorted((tc.function.name, tc.function.arguments) for tc in response_msg.tool_calls))
                if self._last_tool_calls == current_tool_calls_tuple:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0
                self._last_tool_calls = current_tool_calls_tuple

                if self._no_progress_count >= 3:
                     print("\n[系统警告]: Agent 已连续 3 次发起相同的工具调用，可能陷入了无进展循环。")
                     self.memory.add_message("system", "You seem to be making no progress. Please choose a different strategy.")
                     if self.tracer:
                         self.tracer.log_event("loop_warning", {"reason": "repeated_tool_calls"}, step=iteration)
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[系统警告]: 工具 {call_tuple[0]} 带相同参数已连续调用 3 次，可能陷入死循环，中断执行！")
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
                    for tool_call_id, result in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)

                for tool_call in serial_calls:
                    tool_call_id, result = self._execute_tool(tool_call, step_id=iteration)
                    self.memory.add_tool_message(tool_call_id, result)
            else:
                print("\n[系统]: Agent 认为任务已完成，循环结束。")
                break
                
        if iteration >= self.max_steps:
            print(f"\n[系统警告]: Agent 达到最大思考轮次限制 ({self.max_steps}步)，被安全机制强制中断！")
