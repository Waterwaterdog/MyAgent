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
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--plan', action='store_true', help='Enable Plan->Execute mode.')
    group.add_argument('--react', action='store_true', help='Enable ReAct mode.')
    group.add_argument('--hybrid', action='store_true', help='Enable Plan + ReAct hybrid mode.')
    parser.add_argument('--token-budget', type=int, default=4000, help='Max tokens before context compression.')
    args = parser.parse_args()

    print("=======================================")
    print("  Coding Agent 启动 (推免考核项目)")
    if args.hybrid:
        print("  (Plan + ReAct 混合模式已启用)")
    elif args.plan:
        print("  (Plan->Execute 模式已启用)")
    elif args.react:
        print("  (ReAct 模式已启用)")
    print("=======================================")
    
    # 从 .env 文件中加载环境变量
    load_dotenv()
    
    try:
        # 实例化 Agent 的依赖
        llm_client = LLMClient()

        if args.hybrid:
            system_prompt = (
                "你是一个采用 Plan + ReAct 混合架构的编程智能体。\n"
                "你的工作流程分为两个层面：\n"
                "1. **全局规划**: 任务开始前，你会得到一个初始计划。如果执行过程中遇到重大障碍，计划会被动态更新。\n"
                "2. **局部决策 (ReAct)**: 对于计划中的每一个步骤，你将采用 ReAct 模式（决策-行动-观察）来执行。\n"
                "在每一轮执行中：\n"
                "- **决策 (Decision)**: 分析当前步骤的进度，说明你打算调用什么工具。\n"
                "- **行动 (Action)**: 调用工具。\n"
                "- **观察 (Observation)**: 查看工具返回的结果。\n"
                "请确保在每个步骤中都保持清晰的推理过程。当一个步骤完成后，请明确表示该步骤已完成。"
            )
        elif args.react:
            system_prompt = (
                "你是一个采用 ReAct 架构的编程智能体。你的任务是自主解决编程问题。"
                "在每一轮，你都需要进行'决策'和'行动'。"
                "1. **决策 (Decision)**: 简要描述你对当前情况的分析，以及你打算采取的下一步行动。这部分内容将作为普通文本输出。"
                "2. **行动 (Action)**: 调用一个或多个工具来执行你的计划。这部分将通过 Tool Calling 实现。"
                "3. **观察 (Observation)**: 工具执行的结果会作为下一次循环的输入。"
                "持续这个 'Decision -> Action -> Observation' 循环，直到任务完成。"
                "当你认为任务已完全解决时，在最后一次回复中只包含最终答案，不要再调用任何工具。"
            )
        else:
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
        
        # 实例化上下文管理器，注入 LLM 用于后续可能的压缩任务
        memory = Memory(system_prompt, llm_client=llm_client, token_budget=args.token_budget)
        
        # 注入依赖，实例化 Agent
        agent = Agent(llm_client, memory, planning_mode=args.plan, react_mode=args.react, hybrid_mode=args.hybrid)
    except Exception as e:
        print(f"Agent 初始化失败: {e}")
        return
    
    print("\n准备就绪。")
    user_input = input("\n请输入您的编程任务: ")
    # user_input = "读取一个肯定不存在的文件 'non_existent_file.txt'"
    agent.run(user_input)

if __name__ == "__main__":
    main()