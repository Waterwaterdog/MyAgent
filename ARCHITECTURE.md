# Architecture

This document will describe the architecture of the Coding Agent.

## 核心架构设计
当前已完成模块化拆分与工具系统工程化：

- **Agent 主循环 (Agent Loop)**: `coding_agent/core/agent.py` 负责控制整个智能体的运行生命周期，包括状态维护和最大轮次限制。
- **工具注册表 (Tool Registry)**: `coding_agent/tools/registry.py` 通过 `ToolRegistry` 管理工具的动态加载。
- **基础工具接口 (BaseTool)**: `coding_agent/tools/base.py` 定义了标准化工具接口，包括 JSON Schema 生成和参数校验。
- **并行执行运行时 (Parallel Runtime)**: Agent 主循环中实现了依据 `parallel_safe` 属性动态判断并采用 `ThreadPoolExecutor` 并发执行多个安全工具（如并发读取多个文件）的逻辑。
