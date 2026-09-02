

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
