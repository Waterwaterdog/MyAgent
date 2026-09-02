

## Task 07: Plan → Execute 架构
日期：2026-09-02
目标：增加可选的规划模式，使 Agent 能够先将复杂任务分解为结构化计划，然后逐一执行。
修改文件：`coding_agent/core/agent.py`, `coding_agent/planning/planner.py`, `coding_agent/main.py`
核心设计：
1.  **Planner 模块**: 新增 `coding_agent/planning/planner.py`，定义了 `Planner` 类。该类使用专门的系统提示，引导 LLM 将用户任务分解为一个包含 `goal` 和 `steps` 的 JSON 计划。
2.  **Agent 改造**:
    *   在 `Agent` 的 `__init__` 方法中增加了 `planning_mode` 开关。
    *   当 `planning_mode` 开启时，`run` 方法首先调用 `Planner` 创建计划。
    *   创建了 `_execute_step` 方法，它封装了执行单个计划步骤的逻辑（包含一个小的 Agent 循环）。
    *   主 `run` 方法则负责遍历计划，调用 `_execute_step` 来执行每个步骤，并更新步骤状态。
3.  **入口改造**: 修改 `main.py`，增加了 `--plan` 命令行参数，用于从外部启动时激活规划模式。
测试命令：`python -m coding_agent.main --plan`
测试结果：
1.  启动时，Agent 打印出“Plan->Execute 模式已启用”。
2.  输入任务后，Agent 首先生成一个 JSON 格式的计划，并打印到控制台。
3.  然后，Agent 按照计划中的步骤顺序执行，每个步骤都像一个子任务一样被 Agent 的思考循环处理。
4.  所有步骤完成后，Agent 正常终止。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：成功实现了 Plan → Execute 架构。该架构将任务的“规划”和“执行”两个阶段解耦，显著提升了 Agent 处理长链条、多步骤任务的能力和逻辑清晰度。Planner 负责宏观的“做什么”，Executor 负责微观的“怎么做”，是实现更高级 Agent 行为的关键一步。

## Task 08: ReAct 架构
日期：2026-09-02
目标：实现一个可选的 ReAct 模式，使 Agent 能够在“决策-行动-观察”的循环中动态推理和执行任务。
修改文件：`coding_agent/core/agent.py`, `coding_agent/main.py`
核心设计：
1.  **Agent 改造 (`agent.py`)**:
    *   在 `Agent` 的 `__init__` 方法中增加了 `react_mode` 开关，与 `planning_mode` 互斥。
    *   新增 `_run_react_mode` 方法，它包含了 ReAct 模式的核心循环。此循环被明确地构建为 "Reason -> Act -> Observe" 的序列。
    *   在 `run` 方法中增加了逻辑，当 `react_mode` 开启时，调用 `_run_react_mode`。
    *   循环中的打印信息被调整，明确标注出 "[Agent 决策]" (Reason) 和工具调用的 "[执行结果]" (Observation)，使 Agent 的思考过程更透明。
2.  **入口与 Prompt 改造 (`main.py`)**:
    *   使用 `argparse.add_mutually_exclusive_group` 添加了 `--react` 命令行参数，确保了 `--plan` 和 `--react` 不会同时启用。
    *   设计了专门用于 ReAct 模式的系统提示 (System Prompt)。该提示明确指示 LLM 在每一步都必须输出 "决策 (Decision)" 和 "行动 (Action)"，引导模型遵循 ReAct 的思考范式。
    *   根据启动参数 (`--react`, `--plan` 或默认) 动态选择相应的系统提示，并实例化 Agent。
测试命令：`python -m coding_agent.main --react`
测试结果：
1.  启动时，Agent 打印出“ReAct 模式已启用”。
2.  输入任务后，Agent 进入 ReAct 循环。
3.  在每个轮次，Agent 首先打印出 "[Agent 决策]"，内容是 LLM 对当前情况的分析和计划。
4.  紧接着，Agent 发起工具调用 (Action)，并打印 "[执行结果]" (Observation)。
5.  Agent 根据观察到的结果，进入下一个 "决策-行动" 循环，直到任务完成。
6.  整个过程清晰地展示了“思考 -> 行动 -> 观察”的链条，Agent 能够根据工具返回的实时信息动态调整策略。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：成功实现了 ReAct 架构。与 Plan -> Execute 模式相比，ReAct 模式赋予了 Agent 更强的动态适应能力。它不是预先规划好所有步骤，而是在每一步都根据当前环境的反馈进行推理和决策，更适合处理那些探索性强、或无法预先完全规划的任务。
