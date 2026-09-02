# TASK_ALL.md
# 软件工程专业推免项目：编程智能体 Coding Agent 全量优化任务

> 目标：在已有 Demo Coding Agent 代码框架基础上，围绕推免考核题目要求，逐项检查、补齐并验证 Agent 的核心能力与工程创新点。（Demo框架依据task.md实现）
>
> **本文件是总任务清单，不要求一次性全部完成。**
> 后续开发由另一个 AI 按照本文件的编号 **一次只完成一个点**。每完成一个点，必须更新项目记录文件，然后停止，等待用户指挥继续下一点。
>
> 考核题目明确要求：个人独立设计并实现 Coding Agent；Agent 通过大语言模型交互，自主读写文件、执行命令完成编程任务；不得使用现成 Agent 产品封装，也不得使用 LangChain、LlamaIndex、OpenAI Agents SDK、Claude Agent SDK、AutoGen、CrewAI 等 Agent 框架/SDK；重要逻辑必须自行实现，包括对话历史与上下文管理、工具定义与本地执行、模型输出解析、循环终止条件、错误处理。fileciteturn0file0L4-L12
>
> 截止时间为 2026-09-02 24:00（北京时间）；评委会重点关注是否真正理解 Agent 的运行机制，以及能否解释并辩护设计决策。fileciteturn0file0L14-L18 fileciteturn0file0L36-L39

---

## 0. 开发总原则

### 0.1 最重要的约束

1. **不得引入 Agent 框架/SDK**
   - 禁止 LangChain
   - 禁止 LlamaIndex
   - 禁止 OpenAI Agents SDK
   - 禁止 Claude Agent SDK
   - 禁止 AutoGen
   - 禁止 CrewAI
   - 不得通过这些框架间接实现 Agent 核心循环。
2. 可以使用模型厂商 API 客户端、OpenAI 兼容 API、模型原生 Tool Calling，但 Agent 的关键机制必须自己实现。fileciteturn0file0L7-L12
3. API Key、Token 等凭据只能来自环境变量或未入库配置文件，绝对不能提交到仓库、README 或演示视频。fileciteturn0file0L17-L18
4. 不为了“创新”而堆砌复杂代码。所有机制必须能够：
   - 解释为什么需要；
   - 解释如何工作；
   - 给出实际 Demo；
   - 在面试时回答“为什么这样设计”。
5. 每次只修改一个任务点，保证 Git 历史清晰。
6. 每个任务完成后必须：
   - 更新 `README.md`；
   - 更新 `TODO.md`；
   - 更新 `PROGRESS.md`；
   - 更新 `EXPERIMENT.md`；
   - 如涉及架构，则更新 `ARCHITECTURE.md`；
   - 如涉及接口/schema，则更新 `API_SPEC.md`；
   - 如涉及错误，则更新 `ERROR_CODES.md`；
   - 如涉及上下文/memory，则更新对应设计文档；
   - 运行最小测试并记录结果。
7. **不得假装完成。**
   - 如果某项原本已经实现：进行代码审查、测试、补文档，然后标记为“已实现/已验证”；
   - 如果部分实现：只补齐缺失部分；
   - 如果完全没有：新增实现；
   - 如果发现已有实现与本任务冲突：优先修正架构，而不是重复造轮子。

---

# 1. 项目记录机制

在开始第一个任务前，确认以下文件存在；不存在就创建：

```text
README.md
TODO.md
PROGRESS.md
EXPERIMENT.md
ARCHITECTURE.md
API_SPEC.md
ERROR_CODES.md
```

## 1.1 PROGRESS.md

必须维护如下信息：

```text
当前完成点：X / 20
当前状态：进行中 / 已完成 / 阻塞
最近完成：
下一步：
当前已知问题：
最近一次测试：
```

## 1.2 TODO.md

记录：
- 已完成任务；
- 当前任务；
- 下一任务；
- 阻塞项；
- 后续可选优化。

## 1.3 EXPERIMENT.md

每完成一个任务至少记录：

```text
## Task XX
日期：
目标：
修改文件：
核心设计：
测试命令：
测试结果：
遇到的问题：
解决方法：
是否回归测试：
结论：
```

## 1.4 README.md

README 必须持续保持“项目对外介绍”属性，而不是开发日志。

最终 README.txt 有 **1000 汉字以内**限制；正式提交前再从 README.md 提炼成 README.txt。题目明确要求 README.txt 包含仓库地址、运行方式、特色功能等。fileciteturn0file0L19-L23

---

# 2. 总任务路线

共 20 个优化点。

建议严格按照以下顺序推进，因为后面的高级能力依赖前面的基础能力。

| 编号 | 优化点 | 核心价值 |
|---|---|---|
| 01 | Agent 核心循环审计与模块化 | 打牢基础 |
| 02 | Tool Schema + Tool Factory | 工具系统工程化 |
| 03 | Tool 串行/并行执行 | 提升效率 |
| 04 | 标准化 Error Code + 错误包装 | 可控错误处理 |
| 05 | Error → Model 决策闭环 | Agent 自恢复 |
| 06 | 防死循环机制 | 保证 Agent 可终止 |
| 07 | Plan → Execute 架构 | 长任务规划 |
| 08 | ReAct 架构 | 动态推理/行动 |
| 09 | Plan + ReAct 混合架构 | 兼顾规划和动态调整 |
| 10 | 全链路 Trace / Logging | Debug 与可解释性 |
| 11 | 上下文管理与 Token Budget | 控制上下文 |
| 12 | Tool Result 压缩 | 降低上下文膨胀 |
| 13 | API 摘要与 API 文档注入 | 提升工具/API使用质量 |
| 14 | Prompt 静态/动态分离 | 提升 KV Cache 复用 |
| 15 | Memory：短期/中期/长期 | 持久化 Agent 能力 |
| 16 | Memory + KV Cache 复用策略 | 降低重复上下文 |
| 17 | Skill 系统 | 能力模块化复用 |
| 18 | 模块化架构 + 可插拔组件 | 工程完整度 |
| 19 | 综合 Benchmark / Ablation / 回归测试 | 证明优化有效 |
| 20 | Demo、README、视频与面试防守材料 | 最终提交与答辩 |

---

# 3. Task 01 —— Agent 核心循环审计与模块化

## 目标

先不要急着加高级功能。

完整读懂当前 Demo，明确：

```text
User Task
   ↓
Prompt / Context
   ↓
LLM
   ↓
Model Output Parser
   ↓
Tool Call
   ↓
Local Tool Execution
   ↓
Tool Result
   ↓
Context Update
   ↓
LLM
   ↓
...
   ↓
Final Answer
```

## 要检查

- Agent 主循环在哪里；
- 模型调用在哪里；
- Tool Calling 解析在哪里；
- 工具执行在哪里；
- 文件读写在哪里；
- Shell 执行在哪里；
- 错误在哪里处理；
- 循环在哪里结束；
- 上下文在哪里维护。

## 要求

将明显混杂的逻辑拆成合理模块，但不要为了模块化过度拆分。

推荐：

```text
agent/
  core/
    agent_loop.*
    model_client.*
    context.*
    parser.*
  tools/
  runtime/
  memory/
  planning/
  tracing/
```

实际目录以现有项目语言和结构为准，不强行照抄。

## 验收

完成一个最小真实编程任务，例如：

> 创建一个 Python 文件，实现一个函数，然后执行测试。

---

# 4. Task 02 —— Tool Schema + Tool Factory

## 目标

建立真正工程化的 Tool 系统。

每个 Tool 至少定义：

```text
name
description
input_schema
execute()
permission / safety metadata
```

例如：

```json
{
  "name": "read_file",
  "description": "Read a text file",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {"type": "string"}
    },
    "required": ["path"]
  }
}
```

## Tool Factory

不要在 Agent 主循环中写大量：

```text
if tool == "read_file"
if tool == "write_file"
if tool == "shell"
...
```

改成：

```text
ToolFactory
    ↓
ToolRegistry
    ↓
Tool
```

Agent 只关心：

```text
tool_registry.get(name)
tool.validate(args)
tool.execute(args)
```

## 推荐基础 Tool

至少检查：

- `read_file`
- `write_file`
- `edit_file`
- `list_dir`
- `run_command`

可根据已有 Demo 调整。

## 验收

新增 Tool 时不修改 Agent 主循环。

---

# 5. Task 03 —— Tool 串行 / 并行执行

## 核心设计

不是所有 Tool 都必须串行。

例如：

```text
read_file(A)
read_file(B)
read_file(C)
```

如果互不依赖，可以并行。

但是：

```text
read_file(A)
→ 根据 A 内容
→ edit_file(A)
```

必须串行。

## 实现

Tool metadata 增加：

```text
read_only
write
side_effect
parallel_safe
```

原则：

- 多个独立 read → 可并行；
- write → 默认串行；
- edit → 默认串行；
- shell → 根据安全策略决定；
- 有依赖关系 → 串行。

## 特别注意

不能为了并行而并行。

要让模型输出多个 tool call 后，由 runtime 判断：

```text
是否存在依赖？
是否有写冲突？
是否有副作用？
```

## 验收

设计一个同时读取多个文件的测试，证明并行执行确实工作。

---

# 6. Task 04 —— Error Code + 标准错误对象

## 目标

不要让工具直接把 Python Exception / shell 原始错误随便吐给模型或终端。

统一成：

```text
AgentError
  code
  type
  message
  details
  retryable
  suggested_actions
  trace_id
```

## Error Code 示例

```text
E_TOOL_NOT_FOUND
E_TOOL_INVALID_ARGS
E_FILE_NOT_FOUND
E_FILE_PERMISSION
E_FILE_WRITE
E_COMMAND_FAILED
E_COMMAND_TIMEOUT
E_MODEL_API
E_MODEL_PARSE
E_CONTEXT_LIMIT
E_MAX_STEPS
E_INTERNAL
```

## 要求

维护：

```text
ERROR_CODES.md
```

每个 Error Code 解释：

- 含义；
- 触发条件；
- retryable；
- 模型应该怎么处理。

---

# 7. Task 05 —— Error → Model Decision 闭环

这是非常值得展示的创新点。

## 错误处理流程

错误不能直接导致：

```text
terminal:
ERROR!!!
```

而应该：

```text
Tool
 ↓
Exception
 ↓
Error Normalizer
 ↓
Structured AgentError
 ↓
Model Context
 ↓
LLM 决定下一步
```

例如：

```text
E_FILE_NOT_FOUND
retryable=false
suggested_actions=[
  "check parent directory",
  "list directory",
  "verify filename"
]
```

模型可以选择：

```text
list_dir
```

而不是直接退出。

## 但是

不要让模型无限重试。

必须配合 Task 06。

---

# 8. Task 06 —— 防死循环机制

必须实现多层终止机制。

## 机制 1：最大步数

例如：

```text
MAX_STEPS = 25
```

不要把 25 写死在核心逻辑中，应配置化。

## 机制 2：同一 Tool 重复调用限制

例如：

```text
同一个 tool + 相同参数
连续失败 ≥ 3
→ 不允许继续重复
```

## 机制 3：重复状态检测

检测：

```text
tool
arguments
error_code
context_state
```

是否反复出现。

## 机制 4：无进展检测

如果连续多轮：

```text
没有文件变化
没有状态变化
没有新信息
```

则提醒模型：

```text
You are making no progress...
Choose a different strategy.
```

## 机制 5：全局超时

Agent 必须能够退出。

## 验收

构造一个故意失败的任务：

```text
读取不存在的文件
```

证明 Agent 不会无限调用。

---

# 9. Task 07 —— Plan → Execute 架构

增加可选规划模式。

流程：

```text
User Task
 ↓
Planner
 ↓
Plan
 ├─ Step 1
 ├─ Step 2
 ├─ Step 3
 ↓
Executor
 ↓
Verification
 ↓
Update Plan
```

## Plan 必须结构化

例如：

```json
{
  "goal": "...",
  "steps": [
    {
      "id": 1,
      "description": "...",
      "status": "pending"
    }
  ]
}
```

## 注意

Planner 不能执行 Tool。

Planner 负责：

```text
what
```

Executor 负责：

```text
how
```

---

# 10. Task 08 —— ReAct 架构

实现一个可选 ReAct 模式。

核心循环：

```text
Observe
↓
Reason
↓
Act
↓
Observe
↓
...
```

但不要强制输出内部 CoT。

工程上只记录：

```text
decision summary
action
observation
```

而不是要求模型泄露完整隐藏推理。

## 示例

```text
Decision:
Need inspect project structure.

Action:
list_dir

Observation:
...

Next Decision:
Need inspect package configuration.
```

---

# 11. Task 09 —— Plan + ReAct 混合架构

这是推荐最终 Demo 使用的模式。

流程：

```text
                 ┌──────────────┐
                 │    Planner   │
                 └──────┬───────┘
                        ↓
                    Plan Step
                        ↓
                 ┌──────────────┐
                 │    Agent     │
                 │   ReAct Loop │
                 └──────┬───────┘
                        ↓
                    Execute
                        ↓
                    Verify
                        ↓
              ┌─────────┴─────────┐
              ↓                   ↓
           Success              Failure
              ↓                   ↓
        Next Plan Step      Error → Model
```

目标：

- Plan 负责全局；
- ReAct 负责局部动态决策；
- Error 允许模型改变计划。

---

# 12. Task 10 —— Trace / 全链路 Logging

这是非常适合面试展示的能力。

建立：

```text
Trace
 ├── trace_id
 ├── task_id
 ├── step_id
 ├── model_call
 ├── tool_call
 ├── tool_result
 ├── error
 ├── context
 └── final_result
```

## 每次 Agent 运行

生成：

```text
trace_id
```

例如：

```text
20260902-abc123
```

## 日志至少包含

```text
timestamp
trace_id
step
event_type
tool
arguments summary
result summary
latency
error_code
```

## 重点

Trace 必须能回答：

> “这个错误为什么发生？”

以及：

> “Agent 为什么在这里调用这个 Tool？”

---

# 13. Task 11 —— 上下文管理与 Token Budget

上下文不能无限增长。

建立 Context Manager。

至少区分：

```text
System Prompt
User Task
Plan
Recent Messages
Tool Results
Memory
Summaries
```

并维护：

```text
token_budget
```

## 当超过阈值

不要直接截断。

进入：

```text
Context Compression
```

---

# 14. Task 12 —— Tool Result Compression

这是上下文优化的重要点。

Tool 返回可能非常大：

```text
cat 50000 行日志
```

不能全部塞给模型。

建立：

```text
Tool Result
 ↓
Result Analyzer
 ↓
重要信息提取
 ↓
Summary
 ↓
Context
```

例如 shell：

原始结果：

```text
50000 lines
```

模型只需要：

```text
exit code
stderr
key errors
relevant stdout
summary
```

## 注意

原始结果仍然写入 Trace / 文件。

上下文中只放压缩版本。

---

# 15. Task 13 —— API 摘要 + API 文档

如果 Agent 支持外部 API Tool：

不要每轮把完整 API 文档全部塞给模型。

建立：

```text
API Registry
```

存：

```text
name
description
schema
examples
constraints
```

上下文只注入：

```text
必要 API 摘要
```

如果模型调用失败：

```text
错误
→ 根据错误动态补充 API 文档
→ 再调用
```

目标：

> “默认短，出错再补充。”

---

# 16. Task 14 —— Prompt 静态 / 动态分离

将 Prompt 分成：

```text
STATIC
```

和：

```text
DYNAMIC
```

## Static

尽量保持不变：

- Agent identity
- Tool 使用规范
- 输出格式
- 安全规则
- 错误协议

## Dynamic

每轮变化：

- User task
- 当前 plan
- tool result
- memory
- recent state

目标：

```text
STATIC PREFIX
        ↓
尽可能稳定
        ↓
Dynamic Context
```

这样有利于复用模型侧 KV Cache（具体收益依模型/API而定）。

---

# 17. Task 15 —— Memory：短期 / 中期 / 长期

建立三层 Memory。

## Short-term

当前任务：

```text
recent messages
current plan
recent tool results
```

## Mid-term

当前项目：

```text
project conventions
recent decisions
known errors
current progress
```

## Long-term

跨任务：

```text
user preferences
stable coding preferences
reusable project knowledge
```

## 注意

Memory 不是简单把历史聊天全部保存。

必须有：

```text
memory extraction
memory retrieval
memory relevance
memory update
```

---

# 18. Task 16 —— Memory + KV Cache 复用

重点不是“实现真正的模型 KV Cache API”——因为是否能直接控制服务端 KV Cache 取决于模型厂商。

这里做的是：

```text
让输入 Prompt 尽可能稳定
```

例如：

```text
STATIC SYSTEM PROMPT
+
STABLE TOOL SCHEMAS
+
STABLE MEMORY SUMMARY
+
DYNAMIC TASK CONTEXT
```

避免每一轮：

```text
重新生成完全不同的大段 system prompt
```

## 需要在文档里明确

区分：

```text
KV Cache 复用策略
```

和：

```text
模型服务端实际 KV Cache 命中
```

不要虚构后者。

---

# 19. Task 17 —— Skill 系统

设计精美、可复用的 Skill。

Skill 与 Tool 不同：

```text
Tool = 原子能力
Skill = 多 Tool + Prompt + 流程规范
```

例如：

```text
skills/
  debugging/
  testing/
  refactoring/
  code_review/
  project_analysis/
```

## Debug Skill

可能包含：

```text
1. inspect project
2. reproduce error
3. inspect logs
4. identify root cause
5. patch
6. run regression test
```

## Skill Schema

建议：

```text
name
description
when_to_use
instructions
allowed_tools
workflow
```

Skill 由 Agent 选择，而不是写死在主循环。

---

# 20. Task 18 —— 完整模块化架构

最终目标：

```text
                   ┌─────────────┐
                   │     User    │
                   └──────┬──────┘
                          ↓
                 ┌─────────────────┐
                 │  Agent Runtime  │
                 └───────┬─────────┘
                         ↓
              ┌──────────────────────┐
              │ Planner / ReAct      │
              └──────────┬───────────┘
                         ↓
              ┌──────────────────────┐
              │ Context Manager      │
              │ Memory Manager       │
              └──────────┬───────────┘
                         ↓
                 ┌──────────────┐
                 │ Model Client │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Tool Router  │
                 └──────┬───────┘
                        ↓
              ┌─────────────────────┐
              │ Tool Factory/Registry│
              └──────────┬──────────┘
                         ↓
                 ┌──────────────┐
                 │ Local Runtime│
                 └──────────────┘

        ┌──────────────┐
        │ Trace System │
        └──────────────┘

        ┌──────────────┐
        │ Error System │
        └──────────────┘
```

要求：

- Agent Core 不依赖具体 Tool；
- Tool 不依赖 Agent；
- Memory 独立；
- Context 独立；
- Trace 独立；
- Error 独立；
- Model Client 可替换。

---

# 21. Task 19 —— Benchmark / Ablation / 回归测试

不能只说：

> “功能实现了。”

必须证明优化有价值。

建立至少以下测试：

## Baseline

原始 Demo。

## Test A

复杂编程任务成功率。

## Test B

错误恢复成功率。

## Test C

死循环任务。

## Test D

大 Tool Result。

## Test E

多文件读取。

## Test F

Plan + ReAct 长任务。

## 指标

建议记录：

```text
task success rate
average steps
tool calls
repeated tool calls
error recovery rate
context size
compressed context size
latency
```

如果无法准确获得 token 数量，就使用 API 返回的 usage，或者说明估算方式。

## Ablation

例如：

```text
Baseline
+ Error Handling
+ Loop Guard
+ Context Compression
+ Plan/ReAct
+ Memory
```

展示：

```text
稳定性 ↑
上下文 ↓
失败恢复 ↑
平均步数 ↓
```

不能伪造数据，必须真实运行得到。

---

# 22. Task 20 —— 最终 Demo + README + 视频 + 面试防守

最终必须围绕考核要求设计一个 **2 分钟以内**的真实编程任务演示。题目要求视频展示 Agent 完成真实编程任务，并简要讲解功能实现，视频不超过 200 MB。fileciteturn0file0L25-L26

## 推荐 Demo

选择一个 Agent 能在 1~2 分钟内完成、同时能体现高级能力的任务。

例如：

> “这个项目有一个测试失败，请你分析代码和日志，定位问题，修改代码并运行测试验证。”

演示：

```text
User
 ↓
Plan
 ↓
Trace
 ↓
read files
 ↓
run test
 ↓
error
 ↓
Error Code
 ↓
Model decides next action
 ↓
edit file
 ↓
run test
 ↓
success
```

这比简单：

> “创建 hello.py”

更能展示 Agent 的工程能力。

---

# 23. 最终 README.txt 必须满足考核格式

题目明确规定：

```text
README.txt
≤ 1000 汉字
```

至少包含：

```text
1. Git 仓库地址
2. 如何运行
3. 特色功能
4. 其它说明
```

fileciteturn0file0L19-L23

注意：

最终提交的是：

```text
姓名.zip
 ├── README.txt
 └── 视频.mp4
```

题目明确要求提交内容仅包含一个以姓名命名的 zip 文件。fileciteturn0file0L27-L28

---

# 24. 每完成一个 Task 的强制工作流

**这是给后续 AI 最重要的执行规则。**

每次收到：

```text
继续下一个任务
```

必须：

### Step 1：读取状态

首先读取：

```text
TASK_ALL.md
PROGRESS.md
TODO.md
EXPERIMENT.md
README.md
```

确定：

```text
上一次完成到哪里
下一步是什么
是否存在阻塞
```

### Step 2：检查当前代码

不要假设当前代码和任务要求一致。

先搜索：

```text
相关模块
相关函数
相关配置
已有测试
```

### Step 3：实现当前 Task

**只做一个编号。**

例如：

```text
Task 04
```

不要顺便实现：

```text
Task 05
Task 06
Task 07
```

除非当前任务的实现确实需要极少量基础改动。

### Step 4：测试

至少运行：

```text
lint / type check（如果项目支持）
unit test（如果存在）
真实 Agent smoke test
```

### Step 5：更新记录

必须更新：

```text
README.md
TODO.md
PROGRESS.md
EXPERIMENT.md
```

根据任务类型额外更新：

```text
ARCHITECTURE.md
API_SPEC.md
ERROR_CODES.md
MEMORY.md
SKILLS.md
```

### Step 6：给用户简短汇报

告诉用户：

```text
已完成 Task XX
修改了什么
测试是否通过
发现什么问题
下一步是 Task XX+1
```

### Step 7：停止

**不要自动继续下一个 Task。**

等待用户：

```text
继续
```

---

# 25. Git 提交策略

题目明确要求保留完整提交历史，不得压缩或改写已推送历史。fileciteturn0file0L20-L22

因此推荐：

```text
commit 1: baseline
commit 2: task01 agent architecture
commit 3: task02 tool factory
commit 4: task03 parallel tools
...
```

每个任务一个 commit。

Commit message 推荐：

```text
feat(agent): modularize agent loop
feat(tool): add tool factory and schema
feat(runtime): support safe parallel tool execution
feat(error): add structured error codes
feat(agent): route tool errors back to model
feat(runtime): add loop guard
feat(planner): add plan execute mode
feat(agent): add react mode
feat(trace): add end-to-end tracing
feat(context): add context compression
feat(memory): add layered memory
feat(skill): add reusable skill system
test: add agent benchmark
docs: finalize submission materials
```

不要在最后一天 squash。

---

# 26. 绝对禁止事项

1. 不允许使用被题目禁止的 Agent Framework / SDK。fileciteturn0file0L7-L12
2. 不允许把 Agent 核心逻辑全部交给第三方 Agent 产品。
3. 不允许把 API Key 写进代码。
4. 不允许把 API Key 写进 README。
5. 不允许把 API Key 放入视频。
6. 不允许伪造 Benchmark 数据。
7. 不允许声称实现了服务端 KV Cache 命中，除非确有 API/日志证据。
8. 不允许为了“创新”加入无法解释的复杂算法。
9. 不允许只修改 README 而不验证代码。
10. 不允许一个任务还没验证就直接进入下一任务。
11. 不允许每次错误都自动无限 retry。
12. 不允许让巨大 Tool Result 无限制进入上下文。
13. 不允许把完整历史消息永久全部发送给模型而声称“有 Memory”。
14. 不允许通过 prompt 声称支持某功能但代码实际上没有实现。
15. 不允许为了 demo 删除真实错误处理。

---

# 27. 最终创新点优先级

如果时间不足，不要平均用力。

## S 级：必须做好

### S1 Agent 自主闭环

```text
LLM
→ Tool
→ Error
→ Model
→ Tool
→ Verify
```

### S2 Tool Factory + Schema

体现工程化。

### S3 Error Code + Error → Model

体现 Agent 自恢复。

### S4 Loop Guard

体现 Agent Runtime 控制能力。

### S5 Trace

体现“全链路可解释 Debug”。

### S6 Context Compression

体现真正的 Agent 工程问题意识。

### S7 Plan + ReAct

体现 Agent 架构设计。

---

## A 级：强烈推荐

### A1 Tool 并行

### A2 Prompt Static/Dynamic

### A3 Memory 三层

### A4 Skill

### A5 Benchmark/Ablation

---

## B 级：有时间再完善

### B1 API 动态文档

### B2 更复杂的 KV Cache 优化

### B3 更复杂的 Memory Retrieval

### B4 更多 Tool

---

# 28. 面试时必须能够解释的 15 个问题

完成全部任务后，必须自己准备答案。

### Q1
为什么不用 LangChain？

### Q2
你的 Agent Loop 是什么？

### Q3
LLM 如何决定调用哪个 Tool？

### Q4
Tool Schema 为什么需要独立定义？

### Q5
Tool Factory 解决了什么问题？

### Q6
为什么有些 Tool 可以并行，有些必须串行？

### Q7
Tool 报错以后发生什么？

### Q8
如何防止 Agent 无限循环？

### Q9
Plan 和 ReAct 有什么区别？

### Q10
为什么需要 Context Compression？

### Q11
Tool Result 为什么不能全部放进上下文？

### Q12
你的 Memory 分成哪几层？为什么？

### Q13
Prompt 为什么要分静态和动态？

### Q14
Trace 如何帮助你 Debug？

### Q15
为什么这些设计是你自己的 Agent，而不是套了一个 Agent 框架？

---

# 29. 最终验收 Checklist

## 基础能力

- [ ] 能调用 LLM
- [ ] 能读文件
- [ ] 能写文件
- [ ] 能编辑文件
- [ ] 能执行命令
- [ ] 能解析 Tool Call
- [ ] 能循环运行
- [ ] 能结束任务

## 工具系统

- [ ] Tool Schema
- [ ] Tool Factory
- [ ] Tool Registry
- [ ] Tool Validation
- [ ] Tool 串行
- [ ] Tool 并行

## Runtime

- [ ] Error Code
- [ ] Structured Error
- [ ] Error → Model
- [ ] Retry Policy
- [ ] Max Steps
- [ ] Repeated Call Guard
- [ ] No Progress Detection
- [ ] Timeout

## Agent Architecture

- [ ] ReAct
- [ ] Plan
- [ ] Plan + ReAct
- [ ] Verification

## Context

- [ ] Token Budget
- [ ] Context Compression
- [ ] Tool Result Compression
- [ ] Static/Dynamic Prompt

## Memory

- [ ] Short-term
- [ ] Mid-term
- [ ] Long-term
- [ ] Memory retrieval
- [ ] Memory update

## Engineering

- [ ] Trace ID
- [ ] Full-chain logging
- [ ] Modular architecture
- [ ] API Schema
- [ ] Skill System
- [ ] Benchmark
- [ ] Ablation
- [ ] Regression Test

## Submission

- [ ] README.txt ≤ 1000 汉字
- [ ] README.txt 有仓库地址
- [ ] README.txt 有运行方法
- [ ] README.txt 有特色功能
- [ ] API Key 未入库
- [ ] Git 历史完整
- [ ] 视频 ≤ 2 分钟
- [ ] 视频 ≤ 200 MB
- [ ] 最终只有“姓名.zip”
- [ ] ZIP 中只有 README.txt + 视频

---

# 30. 给后续 AI 的最终指令

你现在不是一次性完成 TASK_ALL.md。

你是一个**按阶段执行的科研/工程开发 Agent**。

每次用户让你“继续”时：

```text
1. 读取 TASK_ALL.md
2. 读取 PROGRESS.md
3. 读取 TODO.md
4. 读取 EXPERIMENT.md
5. 确定唯一的下一个未完成 Task
6. 检查当前代码
7. 实现该 Task
8. 测试
9. 更新记录
10. 汇报
11. 停止
```

**绝对不要擅自跨到下一个 Task。**

如果发现下一个 Task 已经实现：

```text
检查实现
→ 补测试
→ 补文档
→ 标记“已实现/已验证”
→ 进入下一个 Task
```

如果发现当前 Task 被前置问题阻塞：

```text
先修复阻塞当前 Task 所必需的问题
→ 记录原因
→ 测试
→ 完成当前 Task
```

如果发现设计冲突：

```text
停止编码
→ 记录冲突
→ 分析最小修改方案
→ 优先保持整体架构一致
```

最终目标不是“代码最多”，而是：

> **构建一个真正由自己实现核心 Runtime 的 Coding Agent，并用可解释、可测试、可追踪的工程机制证明它确实比最初 Demo 更可靠、更高效、更容易 Debug。**

---