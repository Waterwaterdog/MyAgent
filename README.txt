# Coding Agent 项目说明文档

## 1. Git 仓库地址
[在此填入您的仓库地址，例如: https://github.com/username/coding-agent]

## 2. 如何运行
本项目支持 Python 3.8+。
1. 安装依赖：pip install -r coding_agent/requirements.txt
2. 配置环境变量：在 .env 中设置 OPENAI_API_KEY 和 OPENAI_BASE_URL（可选）。
3. 启动：python -m coding_agent.main --hybrid
   - --hybrid: 推荐模式，启用“规划+动态推理”混合架构。
   - 启动后按提示输入编程任务即可。

## 3. 特色功能
本项目完全独立设计并实现了 Agent 核心执行引擎，零依赖 LangChain 等框架。
- 模块化架构：实现了 Agent Runtime 与容器的深度解耦。
- 混合架构 (Plan+ReAct)：兼顾全局规划能力与局部动态适应性。
- 自治愈闭环：通过标准化错误码将系统异常反馈给 LLM，实现故障自主修复。
- 防死循环机制：五层安全防护，确保 Agent 在异常情况下能稳定终止。
- 智能上下文管理：支持 Token 预算控制与语义压缩，有效应对长任务挑战。
- 全链路 Trace 系统：为每次运行生成唯一 ID，完整记录决策链路与性能数据。
- 三层记忆系统：实现了短期对话、中期 Insight 与长期经验的分层管理。
- 专业 Skill 系统：支持将原子工具封装为带 SOP 的高阶技能（如 Debugging）。

## 4. 其它说明
本项目是为推免考核独立开发，重点展示了对 Agent 运行机制的深度掌控及工程化实现水平。所有核心逻辑（循环、上下文、工具分发、追踪）均为自主实现。
