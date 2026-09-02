import json
import time
import concurrent.futures
from collections import defaultdict
from coding_agent.core.model_client import LLMClient
from coding_agent.core.context import Memory
from coding_agent.tools.registry import registry
from coding_agent.core.error import AgentError
from coding_agent.planning.planner import Planner

class Agent:
    """
    Agent 主循环控制器。
    负责接收任务、管理循环迭代、请求 LLM、分发工具调用并返回最终结果。
    """
    def __init__(self, llm_client: LLMClient, memory: Memory, max_steps: int = 25, timeout_seconds: int = 300, planning_mode: bool = False):
        self.llm = llm_client
        self.memory = memory
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.planning_mode = planning_mode
        
        # 防死循环机制所需的状态追踪
        self._tool_call_history = defaultdict(int)
        self._last_tool_calls = None
        self._no_progress_count = 0

        # Plan-Execute 架构
        if self.planning_mode:
            self.planner = Planner(llm_client)
            self.plan = None

    def _execute_tool(self, tool_call):
        tool_name = tool_call.function.name
        tool_args_str = tool_call.function.arguments
        
        print(f"\n[系统]: Agent 发起工具调用 -> {tool_name}")
        print(f"[参数]: {tool_args_str}")

        # 记录工具调用历史 (用于防死循环)
        self._tool_call_history[(tool_name, tool_args_str)] += 1
        
        tool = registry.get_tool(tool_name)
        if not tool:
            error = AgentError(
                code="E_TOOL_NOT_FOUND",
                type="ToolError",
                message=f"工具 '{tool_name}' 不存在。"
            )
            result = json.dumps(error.to_dict(), ensure_ascii=False)
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
            except AgentError as e:
                result = json.dumps(e.to_dict(), ensure_ascii=False)
            except Exception as e:
                error = AgentError(
                    code="E_INTERNAL",
                    type="AgentError",
                    message=f"执行工具时发生未知异常: {e}",
                    details=str(e)
                )
                result = json.dumps(error.to_dict(), ensure_ascii=False)
        
        print(f"[执行结果]:\n{result[:500]}{'...' if len(result)>500 else ''}")
        return tool_call.id, result

    def _execute_step(self, step):
        print(f"\n--- [执行步骤 {step['id']}: {step['description']}] ---")
        self.memory.add_message("system", f"Now, execute this step: {step['description']}")
        
        start_time = time.time()
        iteration = 0
        
        while iteration < self.max_steps:
            iteration += 1
            print(f"\n--- [Agent 思考轮次 {iteration}] ---")

            if time.time() - start_time > self.timeout_seconds:
                print(f"\n[系统警告]: Agent 达到全局超时限制 ({self.timeout_seconds}秒)，被安全机制强制中断！")
                return "timeout"
            
            tools = registry.get_openai_schemas()
            
            try:
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
            except Exception as e:
                print(f"[系统错误]: 请求 LLM 失败: {e}")
                return "llm_error"
            
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
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[系统警告]: 工具 {call_tuple[0]} 带相同参数已连续调用 3 次，可能陷入死循环，中断执行！")
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
                    parallel_results = list(executor.map(self._execute_tool, parallel_calls))
                    for tool_call_id, result in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)

                for tool_call in serial_calls:
                    tool_call_id, result = self._execute_tool(tool_call)
                    self.memory.add_tool_message(tool_call_id, result)
            else:
                print("\n[系统]: Agent 认为步骤已完成。")
                return "completed" # Step completed
                
        return "max_steps_reached"


    def run(self, user_input: str):
        """Agent 主循环 (Agent Loop)"""
        self.memory.add_message("user", content=user_input)
        print(f"\n[用户任务]: {user_input}")
        print("-" * 50)
        
        if self.planning_mode:
            print("\n[系统]: 进入规划模式...")
            self.plan = self.planner.create_plan(user_input)
            
            if not self.plan:
                print("[系统]: 无法创建计划，转为标准执行模式。")
                self._run_without_plan(user_input)
                return

            print("\n[系统]: 已生成计划，开始执行...")
            print(json.dumps(self.plan, indent=2, ensure_ascii=False))
            print("-" * 50)
            
            for step in self.plan["steps"]:
                step["status"] = "in_progress"
                status = self._execute_step(step)
                if status == "completed":
                    step["status"] = "completed"
                    print(f"\n--- [步骤 {step['id']} 完成] ---")
                else:
                    step["status"] = "failed"
                    print(f"\n--- [步骤 {step['id']} 失败，状态: {status}] ---")
                    print("\n[系统]: 由于步骤失败，Agent 停止执行。")
                    break # Stop execution if a step fails
            
            print("\n[系统]: 所有计划步骤已执行完毕。")

        else:
            self._run_without_plan(user_input)

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
                response_msg = self.llm.chat(self.memory.get_messages(), tools)
            except Exception as e:
                print(f"[系统错误]: 请求 LLM 失败: {e}")
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
                
                for tool_call in response_msg.tool_calls:
                    call_tuple = (tool_call.function.name, tool_call.function.arguments)
                    if self._tool_call_history[call_tuple] >= 3:
                        print(f"\n[系统警告]: 工具 {call_tuple[0]} 带相同参数已连续调用 3 次，可能陷入死循环，中断执行！")
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
                    parallel_results = list(executor.map(self._execute_tool, parallel_calls))
                    for tool_call_id, result in parallel_results:
                        self.memory.add_tool_message(tool_call_id, result)

                for tool_call in serial_calls:
                    tool_call_id, result = self._execute_tool(tool_call)
                    self.memory.add_tool_message(tool_call_id, result)
            else:
                print("\n[系统]: Agent 认为任务已完成，循环结束。")
                break
                
        if iteration >= self.max_steps:
            print(f"\n[系统警告]: Agent 达到最大思考轮次限制 ({self.max_steps}步)，被安全机制强制中断！")
