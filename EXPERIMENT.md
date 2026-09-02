# Experiment Log

This file will log the experiments for each task.

## Task 01: Agent 核心循环审计与模块化
日期：2026-09-02
目标：审计当前代码，梳理 Agent 核心循环并模块化。
修改文件：`coding_agent/core/agent.py` 等。
核心设计：拆分了 Agent 主循环、LLM 请求、上下文管理。
测试命令：运行 `python -m coding_agent.main`
测试结果：基础任务能够正常流转并完成。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：基础模块化成功，具备扩展性。

## Task 02: Tool Schema + Tool Factory
日期：2026-09-02
目标：建立工程化的 Tool 系统。
修改文件：`coding_agent/tools/base.py`, `coding_agent/tools/registry.py` 等。
核心设计：定义了 `BaseTool`，包含 `input_schema` 和 `execute`，实现了 `ToolRegistry` 管理所有工具。
测试命令：运行工具调度测试
测试结果：能够动态加载工具和获取 OpenAI JSON Schema。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：工具系统已标准化，方便后续新增工具。

## Task 03: Tool 串行 / 并行执行
日期：2026-09-02
目标：支持互不依赖的 Tool 并行执行以提高效率。
修改文件：`coding_agent/core/agent.py`, `coding_agent/tools/base.py`
核心设计：在 `BaseTool` 中增加了 `parallel_safe` 属性。Agent 主循环中，对于 `parallel_safe=True` 的工具使用 `ThreadPoolExecutor` 并发执行，其他的串行执行。
测试命令：运行包含多个 `read_file` 调用的测试任务。
测试结果：多个 `read_file` 能够并行执行，缩短了总体执行时间。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：并行机制工作正常，能有效提升多文件读取时的性能。

## Task 04: 标准化 Error Code + 错误包装
日期：2026-09-02
目标：将工具的异常输出统一为结构化的 AgentError 对象，替换直接抛出 Exception 或返回错误字符串。
修改文件：`coding_agent/core/agent.py`, `coding_agent/core/error.py`, `coding_agent/tools/cmd_ops.py`, `coding_agent/tools/file_ops.py`, `ERROR_CODES.md`
核心设计：
1. 创建了 `ERROR_CODES.md` 文档，定义了标准的错误码及其含义。
2. 新增了 `coding_agent/core/error.py` 模块，定义了 `AgentError` 类，用于封装错误信息，包括 code, type, message, details, retryable, suggested_actions, trace_id。
3. 修改了 `file_ops.py` 和 `cmd_ops.py`，将底层的 `Exception` 捕获并包装为对应的 `AgentError`。
4. 在 `agent.py` 的 `_execute_tool` 方法中，增加了对 `AgentError` 的捕获。捕获后，将其转换为 JSON 字符串，作为工具执行结果返回给 LLM。这样 LLM 就能在上下文中看到结构化的错误，为下一步决策提供依据。
测试命令：手动测试，例如尝试读取一个不存在的文件。
测试结果：Agent 能够捕获 `E_FILE_NOT_FOUND` 错误，并将其格式化为 JSON 返回。Agent 主循环正常运转。
遇到的问题：无。
解决方法：无。
是否回归测试：是。
结论：成功实现了标准化的错误处理机制。所有工具的错误都被包装成统一的 `AgentError`，这使得 Agent 对错误的感知和处理更加结构化，为后续实现基于错误的自主恢复（Task 05）打下了关键基础。
