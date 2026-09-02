# Memory & Context Design Document

This document describes the design and implementation of the memory and context management system for the Coding Agent.

## 1. Overview

As an autonomous agent performs tasks, the conversation history and tool results can grow significantly. Without proper management, this leads to:
- **Exceeding LLM context limits**: The model may stop accepting new input.
- **Increased cost**: More tokens result in higher API fees.
- **Performance degradation**: Large contexts can slow down reasoning or cause the model to lose track of key information.

The `ContextManager` (formerly `Memory`) is designed to mitigate these issues.

## 2. Core Components

### 2.1 Token Estimation

We use a heuristic approach to estimate tokens without requiring heavy external libraries:
- **Non-ASCII characters (e.g., Chinese)**: Estimated at 1.5 tokens each.
- **ASCII characters**: Estimated at 0.33 tokens each.
- **Formula**: `int(non_ascii * 1.5 + ascii_chars / 3) + 1`

### 2.2 Token Budget

The `ContextManager` maintains a `token_budget` (defaulting to 4000). Before each call to the LLM, the Agent checks the total estimated tokens. If the budget is exceeded, a compression cycle is triggered.

### 2.3 Context Compression (Self-Summarization)

Instead of hard truncation (which loses important context), we use **Self-Summarization**:
1. **Selection**: We split the message history into "Old Messages" and "Recent Messages" (typically the last 4 messages).
2. **Summarization**: The "Old Messages" are sent to the LLM with a prompt to summarize progress, key findings, and current state.
3. **Merging**: If a summary already exists, the new summary is merged with the old one.
4. **Replacement**: The "Old Messages" are removed from the message list, and the new summary is stored.

## 3. Context Structure

When sending messages to the LLM, the context is assembled as follows:

1. **System Prompt**: The core instructions for the Agent.
2. **Context Summary**: If available, the summarized history is injected as a system message: `"Here is a summary of the previous conversation to save context: ..."`
3. **Recent Messages**: The uncompressed messages that are most relevant to the current reasoning step.

## 4. Usage in Agent Loop

```python
# Before each LLM call
if self.memory.get_total_tokens() > self.memory.token_budget:
    self.memory.compress()
    self.tracer.log_event("context_compression", ...)

response = self.llm.chat(self.memory.get_messages(), tools)
```

## 5. Benefits

- **Scalability**: Allows the Agent to handle extremely long tasks without hitting token limits.
- **Explainability**: Summaries provide a clear view of what the Agent thinks has happened so far.
- **Cost Efficiency**: Reduces the average number of tokens per request.
