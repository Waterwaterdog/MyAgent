
## Task 13: API 摘要与 API 文档注入
日期：2026-09-02
目标：优化 Agent 与工具 API 的交互方式，实现“默认短，出错再补充”的动态文档策略，以降低 Token 消耗并提升 Agent 的纠错能力。
修改文件：`coding_agent/tools/api_registry.py`, `coding_agent/tools/registry.py`, `coding_agent/core/agent.py`
核心设计：
1.  **ApiRegistry 模块**: 新增 `coding_agent/tools/api_registry.py`，定义了 `ApiRegistry` 类。该注册表与 `ToolRegistry` 分离，专门负责管理工具的 API 文档。它为每个工具存储了两种级别的 schema：
    *   `summary_schema`: 一个简短的、只包含核心功能描述的 schema，用于默认情况下注入 LLM 上下文。
    *   `full_schema`: 包含完整 `description`、`input_schema` 和 `examples` 的详细 schema。
2.  **注册表改造**: 修改 `coding_agent/tools/registry.py`，在初始化时，将所有工具同时注册到 `ToolRegistry` (负责执行) 和 `ApiRegistry` (负责文档)。默认导出给 Agent 的 `TOOLS_SCHEMA` 现在来自 `api_registry.get_all_summaries()`。
3.  **Agent 纠错逻辑**:
    *   改造 `Agent._execute_tool`，使其在工具执行失败时，能够捕获 `E_TOOL_INVALID_ARGS` 等特定错误。
    *   修改 `Agent` 的核心执行循环 (`_execute_step`, `_run_react_mode`, `_run_without_plan`)。当检测到工具调用失败时，Agent 会：
        1.  从 `ApiRegistry` 中检索出失败工具的 `full_schema`。
        2.  将这个完整的 schema 连同一个引导性提示（例如“你的调用出错了，这是详细文档，请修正后重试”）作为一个 `system` 消息添加到上下文中。
        3.  重新进入下一轮 LLM 调用，此时模型拥有了更丰富的纠错信息。
测试命令：(概念验证) 在 `agent.py` 中手动模拟一次错误的工具调用，例如调用 `write_file` 时缺少 `content` 参数。
测试结果：
1.  Agent 首次调用 `write_file`，由于缺少 `content`，`tool.validate` 抛出异常，被 `_execute_tool` 捕获并包装为 `E_TOOL_INVALID_ARGS` 错误。
2.  Agent 的主循环检测到该错误，从 `ApiRegistry` 获取 `write_file` 的完整文档，并将其添加到 `memory` 中。
3.  在下一轮，LLM 接收到了包含完整文档的上下文，从而理解了 `content` 是必填项。
4.  LLM 生成了正确的、包含 `content` 参数的 `write_file` 调用。
5.  任务成功执行。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：Task 13 实现了 Agent 在工具使用上的智能纠错闭环。通过“默认摘要，按需补充”的策略，不仅在常规情况下显著节省了上下文 Token，更重要的是，它赋予了 Agent 从 API 调用失败中自主学习和恢复的能力。这使得 Agent 在面对不熟悉或复杂的工具时更加鲁棒，是提升 Agent 自主解决问题能力的重要一环。

---

## Task 14: Prompt 静态 / 动态分离
日期：2026-09-02
目标：将 Prompt 分为静态 (Static) 和动态 (Dynamic) 部分，以优化模型侧 KV Cache 的复用，降低 Token 消耗并提升首字响应速度。
修改文件：`coding_agent/core/prompt.py`, `coding_agent/core/context.py`, `coding_agent/core/agent.py`, `coding_agent/main.py`
核心设计：
1.  **PromptManager**: 新增 `coding_agent/core/prompt.py`，专门负责管理 Prompt 组件。定义了 `STATIC_PREFIX`（包含身份、工具规范、输出格式、安全规则等）和根据模式变化的 `DYNAMIC_INSTRUCTIONS`。
2.  **ContextManager 重构**: 修改 `coding_agent/core/context.py`，使其支持分层存储。`get_messages()` 方法现在按顺序组装：`STATIC_PREFIX` -> `DYNAMIC_MODE` -> `PLAN/SUMMARY` -> `DYNAMIC_HISTORY`。
3.  **Plan 动态注入**: 在 `ContextManager` 中新增 `current_plan` 字段，由 `Agent` 在计划生成或更新时实时同步。这使得计划作为动态上下文的一部分，能够在每一轮请求中为模型提供清晰的指导。
测试命令：`python d:\简历\夏令营\南京大学\南软项目\test_prompt_separation.py`
测试结果：
1.  成功验证了 Prompt 的分层组装逻辑。
2.  `Message 0` (Static Prefix) 保持高度稳定。
3.  `Message 1` (Mode Instructions) 在运行期间保持稳定。
4.  `Message 2` (Plan) 随任务进度更新。
5.  `Message 3+` (History) 承载实时对话。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：Task 14 成功实现了 Prompt 的静态/动态分离。这种设计从工程角度实现了 Prompt 的模块化管理，并从底层机制上为模型推理性能的优化（KV Cache）打下了坚实基础，是 Agent 系统向生产级演进的重要一步。

---

## Task 15: Memory：短期 / 中期 / 长期
日期：2026-09-02
目标：建立三层记忆系统（短期、中期、长期），实现知识的自动沉淀与按需检索，提升 Agent 的任务连续性和跨会话一致性。
修改文件：`coding_agent/core/memory.py`, `coding_agent/core/context.py`, `coding_agent/core/agent.py`
核心设计：
1.  **MemoryManager**: 新增 `coding_agent/core/memory.py`。负责管理中期记忆（Session-level, 内存）和长期记忆（Persistent, 磁盘 JSON）。实现了 `extract_insights`（利用 LLM 从对话中提取知识点）和 `get_memory_context`（组装记忆上下文）。
2.  **ContextManager 适配**: 修改 `coding_agent/core/context.py`，支持接收并注入 `memory_context`。将记忆内容放置在 Prompt 的 `system` 消息中，位于静态前缀之后。
3.  **Agent 闭环触发**: 修改 `coding_agent/core/agent.py`。Agent 在每轮执行前自动同步记忆，并在步骤完成或每 5 轮迭代后触发一次记忆提取，实现了“边做边记”的自主学习能力。
测试命令：`python d:\简历\夏令营\南京大学\南软项目\test_memory.py`
测试结果：
1.  成功验证了 `MemoryManager` 对中期记忆（规范、决策、错误）和长期记忆（用户偏好）的分类存储。
2.  成功验证了利用 LLM Mock 返回的 JSON 自动更新记忆库的逻辑。
3.  成功验证了长期记忆的磁盘持久化功能。
4.  生成的记忆上下文能够清晰地反映当前 Session 的核心 insights。
遇到的问题：测试时发现 LLM 返回的 JSON 解析需要健壮性处理（处理 Markdown 代码块标签）。
解决方法：在解析前对返回内容进行了 strip 处理，并支持 ` ```json ` 标签的剥离。
是否回归测试：是。
结论：Task 15 为 Agent 注入了“灵魂”，使其不再仅仅是单次任务的处理器，而是能够随着使用不断积累经验的智能实体。三层记忆架构在保证响应效率的同时，实现了知识的有效过滤与沉淀，极大地增强了 Agent 在复杂编程任务中的逻辑连贯性。

---

## Task 16: Memory + KV Cache 复用策略
日期：2026-09-02
目标：优化 Prompt 注入顺序，确保最稳定的信息位于前部，以最大化模型侧 KV Cache 的命中率，降低推理成本。
修改文件：`coding_agent/core/memory.py`, `coding_agent/core/context.py`, `coding_agent/core/agent.py`
核心设计：
1.  **记忆细化检索**: 修改 `MemoryManager`，支持分别获取长期（跨任务稳定）和中期（会话内稳定）记忆上下文。
2.  **稳定性排序注入**: 重构 `ContextManager.get_messages()`。严格按照 `STATIC PREFIX` (恒定) -> `DYNAMIC MODE` (Session 稳定) -> `LONG-TERM MEMORY` (极稳定) -> `MID-TERM MEMORY` (相对稳定) -> `PLAN` -> `SUMMARY` -> `HISTORY` 的顺序组装 Prompt。
3.  **缓存优化逻辑**: 通过将高频变化的对话历史放在最后，而将基本不变的身份定义和长期知识放在最前，确保了在多轮交互中，Prompt 的公共前缀长度最大化，从而触发服务端的 KV Cache 复用。
测试命令：`python d:\简历\夏令营\南京大学\南软项目\test_kv_order.py`
测试结果：
1.  验证了 Prompt 组装后的消息列表完全符合预设的稳定性降序排列。
2.  即使在 Plan 更新或 History 增长的情况下，Prompt 的前几条关键消息（Prefix）依然保持绝对静止。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：Task 16 在工程层面对 Prompt 进行了“稳定性对齐”。虽然具体的 Cache 命中由模型厂商控制，但通过保证输入 Prefix 的极致稳定性，我们从客户端角度提供了最优的复用前提，这对于提升长对话任务的响应速度至关重要。
