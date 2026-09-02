

## Plan → Execute 架构

为了支持更复杂的长链条任务，项目引入了可选的 Plan → Execute 架构。

- **规划器 (Planner)**: 在 `coding_agent/planning/planner.py` 中实现。当 `planning_mode` 开启时，`Planner` 首先被调用。它通过一个特定的系统提示，让大语言模型（LLM）将用户的宏观任务分解成一个结构化的 JSON 计划。这个计划包含一个总体目标（goal）和一系列具体的步骤（steps）。

- **执行器 (Executor)**: `Agent` 本身在规划模式下扮演执行器的角色。它不再是直接面对模糊的用户任务进行开放式循环，而是接收清晰、明确的计划步骤。`Agent` 会遍历计划中的每一步，并调用 `_execute_step` 方法。

- **步骤执行 (_execute_step)**: 这个方法为每个计划步骤启动一个“微型”的 Agent 循环。在这个微循环中，Agent 的目标是完成当前这一个具体步骤。它会利用现有的工具调用、错误处理和防死循环机制来确保步骤的顺利完成。

这个架构的核心优势在于**责任分离**：
- **Planner 关注“做什么”（What）**: 它负责战略层面的任务分解，将一个模糊的、可能需要多步才能解决的问题，拆解成一系列清晰、可执行的子任务。
- **Executor 关注“怎么做”（How）**: 它负责战术层面的任务执行，聚焦于如何利用现有工具集高效、可靠地完成每一个具体的子任务。

通过这种方式，Agent 的行为变得更加可预测、可控，也更容易调试。

---

## ReAct 架构

ReAct (Reason + Act) 是一种使 Agent 能够在动态环境中进行推理和行动的范式。

- **核心循环**: 在 `react_mode` 下，Agent 的主循环被明确定义为“决策 (Decision) -> 行动 (Action) -> 观察 (Observation)”。
- **决策 (Reasoning)**: Agent 在执行任何动作前，必须先在内部（或显式输出）进行推理，分析当前的状况、已有的信息以及下一步的最优路径。
- **行动 (Acting)**: 根据决策结果，Agent 发起具体的工具调用。
- **观察 (Observation)**: Agent 接收工具执行后的反馈（包括数据和错误信息），并将其作为下一轮决策的输入。

ReAct 架构的优势在于其**动态适应性**，它能够处理那些在开始前无法预见所有步骤的任务，根据实时反馈灵活调整策略。

---

## Plan + ReAct 混合架构

这是本项目的核心架构，旨在结合战略规划与动态战术调整的优势。

- **全局规划 (Strategic Layer)**: 由 `Planner` 负责。在任务开始前，生成一个初始的多步计划。这保证了 Agent 对长链条任务有一个清晰的整体认知 and 目标感。
- **局部动态执行 (Tactical Layer)**: 对于计划中的每一个步骤，Agent 都采用 ReAct 模式来执行。这意味着在完成每一个具体的子任务时，Agent 依然保持着高度的警觉 and 推理能力，而不是死板地执行预设指令。
- **动态计划调整 (Self-Correction)**: 当某个步骤执行失败，或者 ReAct 循环中发现了与原计划冲突的新信息时，Agent 会触发 `Planner.update_plan`。此时，Agent 会回退到全局规划层面，根据当前的实际进展 and 最新的上下文信息，重新生成剩余的计划步骤。

这种“**大局观 + 动态推理 + 自我修正**”的组合，使 Coding Agent 具备了在复杂真实编程场景中长期稳定工作的能力。

---

## 全链路 Trace / Logging 系统

为了提升 Agent 的**可解释性 (Explainability)** 和 **Debug 效率**，项目实现了一套完整的全链路追踪系统。

- **追踪标识 (Trace ID)**: 每次 Agent 运行都会生成一个唯一的 `trace_id`（例如 `20260902-abc123`），用于关联该次运行中的所有事件。
- **结构化事件 (Trace Events)**: 系统记录了任务执行过程中的每一个关键动作，包括：
    - `task_start`: 任务启动及其初始参数。
    - `plan_generated` / `plan_updated`: 全局计划的生成与动态调整。
    - `model_call`: 大模型调用的输入摘要、输出摘要及其延迟 (Latency)。
    - `tool_call`: 工具调用的名称及其具体参数。
    - `tool_result`: 工具执行的结果摘要、延迟以及可能产生的错误码 (`error_code`)。
    - `loop_detected` / `loop_warning`: 防死循环机制触发的预警和动作。
    - `final_result`: 任务的最终交付结果及其总延迟。
- **持久化存储**: 所有的 Trace 信息都会以结构化 JSON 的形式自动保存到 `logs/traces/` 目录下。

该系统的核心价值在于：
1. **故障回溯**: 当 Agent 报错或陷入循环时，可以通过 Trace 日志精确还原当时的上下文、模型输入和工具反馈，快速定位问题。
2. **性能分析**: 记录了每一轮模型请求和工具执行的耗时，方便识别性能瓶颈。
3. **行为审计**: 完整记录了 Agent 的决策链路，为 Agent 的行为提供了可审计的证据，增强了面试时的说服力。

---

## 上下文管理与 Token 预算 (Context Management)

随着任务复杂度的增加，对话历史和工具返回结果会迅速消耗 Token。为了保证 Agent 的长期运行并降低成本，项目引入了 `ContextManager`。

- **Token 估算**: 基于字符类型的启发式算法，实时监控当前上下文的 Token 消耗情况。
- **预算管理 (Token Budget)**: 用户可以配置 `token_budget`（默认 4000），当估算的 Token 总数超过预算时，系统会自动触发压缩逻辑。
- **上下文压缩 (Context Compression)**: 
    - 系统不会简单地截断历史，而是调用 LLM 对较旧的对话和工具结果进行**语义总结**。
    - 总结后的内容（Summary）会被注入到 System Prompt 之后，作为后续轮次的参考背景。
    - 这种方式在极大缩减 Token 占用的同时，保留了任务的关键进展和历史背景。
- **优先级保留**: 在压缩时，系统会强制保留最近的几轮对话（Recent Messages），确保 Agent 对当前正在进行的子任务有精确的记忆。
79→
80→---

## 工具结果分析与压缩 (Result Analyzer)

除了全局的上下文总结，项目还实现了针对单个工具输出的即时压缩机制。

- **ResultAnalyzer**: 专门负责处理那些返回巨大内容的工具（如 `cat` 大文件、`run_command` 输出海量日志）。
- **智能压缩策略**:
    - **通用截断**: 对超长字符串采用“头部保留 + 中间省略 +尾部保留”的策略，确保关键的开始和结束信息不丢失。
    - **结构化优化**: 针对 `run_command` 等复杂输出，提取 `exit_code`、`stderr` 和 `stdout` 的关键部分，重新组装成对 LLM 友好的精简摘要。
- **双轨制记录**: 压缩后的摘要被放入 LLM 上下文中以节省 Token，而**原始的完整输出**则被记录在全链路 Trace 系统中，确保了调试时的信息无损。

---

## Prompt 静态 / 动态分离 (Prompt Separation)

为了充分利用大模型侧的 **KV Cache** 机制并提升推理效率，项目对 Prompt 的构建方式进行了深度优化。

- **静态前缀 (Static Prefix)**: 在 `coding_agent/core/prompt.py` 中定义。这部分包含 Agent 的身份定义、通用的工具使用规范、标准化的输出格式、安全规则以及错误处理协议。这些内容在整个任务生命周期中是完全不变的，作为所有请求的起始部分（Prefix），极大地提高了 KV Cache 的命中率，降低了首字延迟。
- **动态指令 (Dynamic Instructions)**: 根据用户选择的运行模式（Standard, ReAct, Plan, Hybrid）动态生成的指令。这部分内容在选定模式后也是相对稳定的。
- **任务感知上下文 (Task Context)**: 包括当前的任务计划（Plan）、对话摘要（Summary）以及最近的对话历史。这部分内容会随着任务推进而变化，被放置在 Prompt 的后部。
- **分层注入与稳定性排序**: `ContextManager` 在组装消息列表时，遵循 `STATIC PREFIX -> DYNAMIC MODE -> LONG_TERM -> MID_TERM -> PLAN -> SUMMARY -> HISTORY` 的稳定性排序。这种设计通过将最稳定的信息放置在 Prompt 的前部，最大化了模型侧 KV Cache 的命中率，从而在长对话中显著降低了首字延迟和推理开销。

---

## 三层记忆系统 (Layered Memory System)

为了提升 Agent 的长期稳定性和个性化能力，项目实现了一套分层记忆系统，详细设计见 [MEMORY.md](file:///d:/简历/夏令营/南京大学/南软项目/MEMORY.md)。

- **短期记忆 (Short-term)**: 维护在 `ContextManager` 中，包含即时对话和执行计划。支持自动语义压缩以应对 Token 预算超限。
- **中期记忆 (Mid-term)**: 维护在 `MemoryManager` 的内存结构中，存储当前会话的项目规范、关键决策和已知错误。通过定期调用 LLM 从对话中提取 insights 实现自动更新。
- **长期记忆 (Long-term)**: 持久化在磁盘上的 JSON 文件中，存储跨会话的用户偏好和通用经验知识。
- **记忆提取与注入**: Agent 在执行过程中自动识别并沉淀知识，并在每一轮推理前将相关的记忆片段动态注入到上下文的特定位置。

---

## Skill 系统 (Skill System)

为了将 Agent 从简单的“工具调用者”提升为具备专业知识的“专家系统”，项目引入了可复用的 Skill 机制。

- **Skill vs. Tool**:
    - **Tool**: 原子能力，如 `read_file`, `run_command`。Agent 拥有工具箱，但可能缺乏高效组合它们的领域经验。
    - **Skill**: 高阶能力封装，如 `Debugging`。它不仅包含工具集，还硬编码了**专家经验 (Instructions)** 和 **标准工作流 (Workflow)**。
- **架构设计**: 
    - 基础定义在 `coding_agent/skills/base.py`。每个 Skill 类明确定义了 `name`, `description`, `instructions`, `allowed_tools` 和 `workflow`。
    - 统一通过 `SkillRegistry` 进行管理和加载。
- **动态激活闭环**:
    1. **认知与激活**: Agent 的静态 Prompt 中注入了可用 Skill 的列表与说明。当 Agent 判断当前任务需要专业流程时，它会主动调用特定的 `use_skill` 工具。
    2. **上下文重构**: 激活后，Agent 会将该 Skill 的详细指令和工作流注入系统上下文，指导接下来的思考。
    3. **工具集收敛**: 为防止 Agent 偏离标准流程，激活 Skill 后，可供大模型使用的工具集会被严格限制为该 Skill 定义的 `allowed_tools` 白名单。
- **价值**: 通过引入 SOP (标准作业程序)，大幅提升了复杂任务（如定位 Bug 并修复）的执行成功率和可控性，是实现生产级 Agent 的关键一步。

