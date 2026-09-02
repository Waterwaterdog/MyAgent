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
from coding_agent.core.prompt import PromptManager

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
    mode = "standard"
    if args.hybrid:
        print("  (Plan + ReAct 混合模式已启用)")
        mode = "hybrid"
    elif args.plan:
        print("  (Plan->Execute 模式已启用)")
        mode = "plan"
    elif args.react:
        print("  (ReAct 模式已启用)")
        mode = "react"
    print("=======================================")
    
    # 从 .env 文件中加载环境变量
    load_dotenv()
    
    try:
        # 实例化 Agent 的依赖
        llm_client = LLMClient()

        # 使用 PromptManager 进行静态/动态分离
        static_prompt = PromptManager.get_static_prefix()
        dynamic_instructions = PromptManager.get_mode_instructions(mode)
        
        # 实例化上下文管理器，注入 LLM 用于后续可能的压缩任务
        memory = Memory(static_prompt, dynamic_instructions, llm_client=llm_client, token_budget=args.token_budget)
        
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