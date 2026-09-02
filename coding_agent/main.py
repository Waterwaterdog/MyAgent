import os
import sys
import argparse

# 将项目根目录（coding_agent的上级目录）添加到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
from coding_agent.core.agent import Agent
from coding_agent.core.context import Memory
from coding_agent.core.model_client import LLMClient

def main():
    parser = argparse.ArgumentParser(description="Coding Agent for Nanjing University's summer camp project.")
    parser.add_argument('--plan', action='store_true', help='Enable Plan->Execute mode.')
    args = parser.parse_args()

    print("=======================================")
    print("  Coding Agent 启动 (推免考核项目阶段 3)")
    if args.plan:
        print("  (Plan->Execute 模式已启用)")
    print("=======================================")
    
    # 从 .env 文件中加载环境变量
    load_dotenv()
    
    try:
        # 实例化 Agent 的依赖
        llm_client = LLMClient()
        system_prompt = (
            "你是一个强大的编程智能体 (Coding Agent)，你的核心职责是自主解决编程任务。\n"
            "你可以通过提供的工具读写本地文件、执行命令。\n"
            "**错误处理是你的关键能力**：\n"
            "1. 当工具执行返回错误时，它会以包含 'code', 'message', 'details', 和 'suggested_actions' 的 JSON 对象形式提供。\n"
            "2. **你必须优先采纳 'suggested_actions' 提供的建议来修复问题**。这是强制性要求，而不是一个选项。\n"
            "3. 只有在 'suggested_actions' 为空或尝试后仍然失败的情况下，你才应该基于 'message' 和 'details' 自行分析并制定新的计划。\n"
            "4. **禁止直接向用户报告可恢复的错误**。你的任务是解决问题，而不是简单地传递错误信息。\n"
            "例如，如果 `read_file` 失败并建议 `list_files`，你必须立即调用 `list_files` 来检查目录内容，而不是告诉用户“文件未找到”。\n"
            "在你认为任务已完全解决、不再需要调用任何工具时，才输出对用户的最终总结回复。"
        )
        memory = Memory(system_prompt)
        
        # 注入依赖，实例化 Agent
        agent = Agent(llm_client, memory, planning_mode=args.plan)
    except Exception as e:
        print(f"Agent 初始化失败: {e}")
        return
    
    print("\n准备就绪。")
    user_input = input("\n请输入您的编程任务: ")
    # user_input = "读取一个肯定不存在的文件 'non_existent_file.txt'"
    agent.run(user_input)

if __name__ == "__main__":
    main()