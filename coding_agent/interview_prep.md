# 阶段 12 与面试准备：英文介绍与 Q&A 辩护指南

## 英文面试介绍 (不超过 1 分钟)

**英文原稿：**
"Good morning, professors. I'm honored to present my project: a lightweight Coding Agent built from scratch. 
Instead of relying on heavy frameworks like LangChain, I independently implemented the core Agent Loop, context memory, and tool dispatching mechanism using OpenAI's native Tool Calling.
When given a task, the agent can autonomously write code, execute local commands to run tests, and fix bugs based on the error output. 
The core highlight of my design is its transparency and security. I implemented a sandbox directory to prevent path traversal and a command blacklist to block dangerous operations.
Through this project, I deeply understand how LLMs interact with local environments and how to build a reliable autonomous system. Thank you!"

**对应中文翻译：**
“各位教授早上好。很荣幸介绍我的项目：一个从零构建的轻量级编程智能体。
我没有依赖像 LangChain 这样笨重的框架，而是利用 OpenAI 原生的工具调用功能，独立实现了核心的 Agent 循环、上下文记忆和工具调度机制。
当接到任务时，智能体能够自主编写代码，执行本地命令来运行测试，并根据错误输出修复 Bug。
我设计的核心亮点是其透明性和安全性。我实现了沙箱目录以防止路径穿越，并设置了命令黑名单来拦截危险操作。
通过这个项目，我深刻理解了大模型如何与本地环境交互，以及如何构建一个可靠的自主系统。谢谢！”

**面试官可能追问的 5 个英文问题及回答思路：**
1. **Why didn't you use LangChain?** (为什么不用 LangChain？)
   *Answer:* Because building it from scratch allows me to fully understand the under-the-hood mechanisms, such as how tool schemas are parsed and how the Agent Loop handles context limits. It also makes the system much lighter and easier to debug.
2. **How does your agent fix errors autonomously?** (你的 Agent 如何自主修复错误？)
   *Answer:* When a local command fails, the dispatcher captures the stderr and exit code, sending them back to the LLM. The LLM acts as a reasoning engine, analyzes the error, and calls the `edit_file` tool to apply a fix.
3. **How do you prevent infinite loops?** (如何防止无限循环？)
   *Answer:* I implemented a hard limit on the maximum iterations (e.g., 15 rounds) within the Agent Loop. If the limit is reached, the system forces a termination to prevent infinite loops and save token costs.
4. **How do you ensure the agent doesn't delete important system files?** (如何确保 Agent 不会删除重要的系统文件？)
   *Answer:* All file operations are restricted to the current working directory using absolute path validation. I also implemented a blacklist for dangerous terminal commands like `rm -rf`.
5. **What was the biggest challenge?** (最大的挑战是什么？)
   *Answer:* The biggest challenge was context management. Sometimes command outputs are too long and exceed the token limit. I solved this by truncating excessively long stdout/stderr before appending them to the memory.

---

## 评委深度 Q&A 辩护指南 (中文)

**1. 系统整体架构解释**
- **简单版**：我的系统分为 LLM 通信层、内存层、工具执行层和核心 Agent Loop。
- **正式版**：系统采用高度模块化设计。`llm.py` 封装 API 调用；`memory.py` 管理多轮对话历史；`tools` 目录定义了本地函数并通过 `registry.py` 向 LLM 暴露 JSON Schema；`agent.py` 作为大脑，负责循环读取响应、判断工具调用并分发执行，最终将结果写回内存。

**2. 为什么不用 LangChain / Agents SDK？**
- **简单版**：为了符合题目要求，也是为了彻底搞懂 Agent 底层原理。
- **正式版**：现成框架往往过度封装，隐藏了 prompt 组装和 tool parsing 的细节，导致 Debug 困难。自行实现不仅满足了考核要求，更让我深刻理解了 Tool Calling 的本质：它不过是 LLM 返回的一段结构化 JSON，系统需要自行拦截、执行并反馈。这种透明的设计在真实工程中更可控。

**3. Tool Calling 是怎么工作的？**
- **简单版**：我告诉模型有哪些工具，模型返回需要调用的工具名和参数，我在本地运行后把结果告诉它。
- **正式版**：首先，我在 `registry.py` 中按照 OpenAI 规范定义了各个工具的描述和参数 Schema。每次请求时将 Schema 发给 LLM。如果 LLM 决定调用工具，会返回 `finish_reason="tool_calls"` 以及工具名和 JSON 参数。我的分发器解析参数，执行对应的 Python 函数，最后将结果以 `role="tool"` 的消息追加到上下文中再次请求 LLM。

**4. Context Management (上下文管理) 是怎么做的？如果太长怎么办？**
- **简单版**：用一个列表保存所有对话，如果文件读取或命令输出太长，我会截断它们。
- **正式版**：我通过 `Memory` 类维护一个标准的 OpenAI Messages 列表。为了防止 Token 爆炸，我在 `read_file` 和 `run_command` 的返回值中加入了长度限制（例如截断超过 5000 字符的部分）。未来还可以引入文本摘要算法对过长的历史记录进行压缩。

**5. 如何防止无限循环？**
- **简单版**：我加了一个最大轮次计数器。
- **正式版**：在 `Agent.run` 的 `while True` 循环中，我设置了 `max_iterations` 阈值（比如 15 次）。每次调用 LLM 计数加一，超过阈值直接 `break` 并抛出警告。这既能防止死循环，又能控制 API 成本。

**6. 如何保证文件操作和命令执行的安全？**
- **简单版**：限制文件只能在当前目录操作，屏蔽了危险命令。
- **正式版**：
  1. **目录穿越防护**：在 `file_ops.py` 中，所有传入的路径都会与 `os.getcwd()` 拼接并取绝对路径，检查其是否以工作目录为前缀。否则抛出权限异常。
  2. **命令拦截**：维护了一个 `FORBIDDEN_COMMANDS` 黑名单。
  3. **超时控制**：`subprocess.run` 设置了 `timeout=10`，防止 Agent 运行了阻塞进程（如开启 Web Server）导致主循环卡死。

**7. 如果模型输出错误 Tool Call（例如参数缺失）怎么办？**
- **简单版**：捕获异常，把错误信息作为工具结果返回给 LLM，让它自己纠正。
- **正式版**：我的工具调度器包含完整的 `try-except` 块。如果发生 `JSONDecodeError` 或缺少必填参数，调度器不会崩溃，而是返回形如“错误：工具参数解析失败”的字符串。这个字符串会作为 Tool Message 回传给 LLM，强大的模型通常会在下一轮自动修正其参数格式。

**8. 如果继续开发，还可以增加什么？**
- **正式版**：
  1. **基于 AST 的代码修改工具**：目前的字符串替换 `edit_file` 对大范围重构容易失效，未来可引入基于 diff 或抽象语法树的修改工具。
  2. **多 Agent 协作**：引入 Planner Agent 专门负责拆解复杂任务，Coder Agent 负责写代码，Reviewer Agent 负责检查。
  3. **沙箱容器化**：将命令执行放入真正的 Docker 容器中，实现彻底的系统级隔离。