# Error Codes

This document defines the standardized error codes for the Coding Agent.

## Error Code Schema

Each error is represented by a structured `AgentError` object with the following fields:

- `code`: A unique identifier for the error (e.g., `E_FILE_NOT_FOUND`).
- `type`: The category of the error (e.g., `ToolError`, `ModelError`).
- `message`: A human-readable error message.
- `details`: Any additional details about the error.
- `retryable`: A boolean indicating if the operation can be retried.
- `suggested_actions`: A list of suggested actions for the model to take.
- `trace_id`: The trace ID for the current agent run.

## Error Codes

| Code | Type | Message | Retryable | Suggested Actions |
|---|---|---|---|---|
| `E_TOOL_NOT_FOUND` | `ToolError` | The requested tool could not be found. | `false` | - Verify the tool name. <br> - List available tools. |
| `E_TOOL_INVALID_ARGS` | `ToolError` | The arguments provided to the tool are invalid. | `false` | - Check the tool's schema for required arguments. <br> - Correct the arguments and retry. |
| `E_FILE_NOT_FOUND` | `FileError` | The specified file could not be found. | `false` | - Verify the file path. <br> - List files in the directory to check if the file exists. |
| `E_FILE_PERMISSION` | `FileError` | Insufficient permissions to access the file. | `false` | - Check file permissions. |
| `E_FILE_WRITE` | `FileError` | An error occurred while writing to the file. | `true` | - Retry writing to the file. |
| `E_COMMAND_FAILED` | `CommandError` | The executed command failed. | `false` | - Check the command for errors. <br> - Inspect the command's output for more details. |
| `E_COMMAND_TIMEOUT` | `CommandError` | The command execution timed out. | `true` | - Retry the command. <br> - Increase the timeout. |
| `E_MODEL_API` | `ModelError` | An error occurred with the model's API. | `true` | - Retry the API call. |
| `E_MODEL_PARSE` | `ModelError` | An error occurred while parsing the model's output. | `false` | - Inspect the model's output. |
| `E_CONTEXT_LIMIT` | `AgentError` | The context limit has been reached. | `false` | - Summarize the context. |
| `E_MAX_STEPS` | `AgentError` | The maximum number of steps has been reached. | `false` | - Stop the agent. |
| `E_INTERNAL` | `AgentError` | An internal error occurred. | `false` | - Inspect the agent's logs. |
