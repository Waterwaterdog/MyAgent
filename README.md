# Coding Agent

本项目是一个独立设计并实现的轻量级编程智能体（Coding Agent）。它无需依赖任何第三方 Agent 框架（如 LangChain 或 AutoGen），直接通过大语言模型的原生 Tool Calling 能力，自主完成对本地文件的读取、修改、写入，以及终端命令的执行。Agent 能够理解复杂的编程任务，通过多轮“思考-调用工具-观察结果”的闭环，自动编写代码、运行测试并修复错误。

## 🌟 特色功能

本项目严格遵循从零构建的核心原则，已实现以下关键特性：

- **完全自主的核心控制循环 (Agent Loop)**: 不依赖第三方 SDK，深度把控 LLM 请求、工具调用解析和上下文迭代的生命周期。
- **标准化工具工厂 (Tool Factory & Schema)**: 统一且高度可扩展的 `BaseTool`，支持参数的自动校验与大模型 JSON Schema 的一键导出。
- **智能并发执行引擎**: 自动区分 `read_only`（安全并发）与写操作。当大模型同时需要读取多个文件时，支持通过线程池进行并发执行，极大缩短响应延迟。
- **Error -> Model 自治愈闭环**: 标准化了全系统的错误码（`AgentError`），底层工具引发的系统异常不会直接抛出导致崩溃，而是被包装为结构化错误反馈给大模型，供其在下一轮进行自主修复。
- **多层防死循环机制 (Loop Guard)**: 通过最大步数限制、重复工具调用检测、无进展探测和全局超时等多层防御机制，确保 Agent 在面对复杂或意外情况时能够稳定终止，避免了失控和资源浪费。
- **可选的规划与执行架构 (Plan → Execute)**: 面对复杂任务，可启用规划模式。Agent 会首先将任务分解为详细的、结构化的步骤计划，然后严格按照该计划逐一执行。这种架构将战略规划与战术执行分离，显著提升了处理长链条任务的成功率和逻辑清晰度。
- **动态推理与行动架构 (ReAct)**: 可选的 ReAct 模式使 Agent 能够在“决策(Reason)-行动(Act)-观察(Observe)”的循环中动态推理。Agent 在每一步都明确阐述其决策过程，然后执行工具调用，并根据观察到的结果调整下一步策略，这使其更具适应性和透明度。
- **安全沙箱与自我保护机制**: 实现了严格的目录穿越防护（所有文件操作限定在指定工作区）与高风险终端命令（如 `rm -rf`）拦截。

## 🚀 运行方式

### 1. 安装依赖
确保系统已安装 Python 3.8 或更高版本。
```bash
pip install -r coding_agent/requirements.txt
```

### 2. 配置环境变量
在项目根目录（或 `coding_agent` 目录下）配置 API 密钥：
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your_api_key"

# Linux / macOS
export OPENAI_API_KEY="your_api_key"
```
*(注：项目同样兼容阿里云百炼、DeepSeek 等 OpenAI 格式接口。如果使用兼容接口，请同时配置 `OPENAI_BASE_URL`)*

### 3. 启动 Agent
在项目根目录执行以下命令启动：
```bash
python -m coding_agent.main
```
启动后，在终端提示符处输入您的编程任务，Agent 将自动开始思考与执行。

### 4. 启用高级模式 (可选)
启动时支持多种执行模式：
- `--plan`: 启用先规划、后执行模式。
- `--react`: 启用 ReAct 动态推理循环模式。
- `--hybrid`: 启用 Plan + ReAct 混合架构模式（推荐）。

示例：
```bash
python -m coding_agent.main --hybrid
```

## 🔗 Git 仓库地址
*(待最终提交时填写)*

---
*注：本项目文档和核心能力正根据 `task_all.md` 的路线图逐步完善中，当前已完成至 Task 09。*
