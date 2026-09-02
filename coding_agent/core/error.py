from typing import List, Optional, Literal

class AgentError(Exception):
    def __init__(
        self,
        code: str,
        type: str,
        message: str,
        details: Optional[str] = None,
        retryable: bool = False,
        suggested_actions: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.code = code
        self.type = type
        self.message = message
        self.details = details
        self.retryable = retryable
        self.suggested_actions = suggested_actions or []
        self.trace_id = trace_id

    def to_dict(self):
        return {
            "code": self.code,
            "type": self.type,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
            "suggested_actions": self.suggested_actions,
            "trace_id": self.trace_id,
        }
