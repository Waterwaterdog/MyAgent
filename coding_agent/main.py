import os
import sys

# 将项目根目录（coding_agent的上级目录）添加到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
from coding_agent.core.agent import Agent
from coding_agent.core.context import Memory
from coding_agent.core.model_client import LLMClient

def main():
    print("=======================================")
    print("  Coding Agent 启动 (推免考核项目阶段 3)")
    print("=======================================")
    
    # 从 .env 文件中加载环境变量
    load_dotenv()
    
    try:
        # 实例化 Agent 的依赖
        llm_client = LLMClient()
        system_prompt = (
            "你是一个强大的编程智能体 (Coding Agent)。\n"
            "你可以通过提供的工具读写本地文件、执行命令，从而帮助用户完成真实的编程任务。\n"
            "遇到错误时，请尝试自己分析并修复代码。\n"
            "如果你认为任务已经完全解决，不需要再调用工具时，请直接输出对用户的总结回复即可。"
        )
        memory = Memory(system_prompt)
        
        # 注入依赖，实例化 Agent
        agent = Agent(llm_client, memory)
    except Exception as e:
        print(f"Agent 初始化失败: {e}")
        return
    
    print("\n准备就绪。")
    user_input = input("\n请输入您的编程任务: ")
    if user_input.strip():
        agent.run(user_input)

if __name__ == "__main__":
    main()