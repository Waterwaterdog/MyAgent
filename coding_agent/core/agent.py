import json
import concurrent.futures
from coding_agent.core.model_client import LLMClient
from coding_agent.core.context import Memory
from coding_agent.tools.registry import registry
from coding_agent.core.error import AgentError

class Agent:
    """
    Agent 主循环控制器。
    负责接收任务、管理循环迭代、请求 LLM、分发工具调用并返回最终结果。
    """
    def __init__(self, llm_client: LLMClient, memory: Memory):
        self.llm = llm_client
        self.memory = memory

    def _execute_tool(self, tool_call):
        tool_name = tool_call.function.name
        tool_args_str = tool_call.function.arguments
        
        print(f"\n[系统]: Agent 发起工具调用 -> {tool_name}")
        print(f"[参数]: {tool_args_str}")
        
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

    def run(self, user_input: str):
        """Agent 主循环 (Agent Loop)"""
        self.memory.add_message("user", content=user_input)
        print(f"\n[用户任务]: {user_input}")
        print("-" * 50)
        
        max_iterations = 15  # 防止无限循环的安全机制
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- [Agent 思考轮次 {iteration}] ---")
            
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
                
        if iteration >= max_iterations:
            print("\n[系统警告]: Agent 达到最大思考轮次限制，被安全机制强制中断！")
