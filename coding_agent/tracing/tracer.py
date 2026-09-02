import json
import time
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

class TraceEvent:
    def __init__(self, event_type: str, data: Dict[str, Any], step: Optional[int] = None):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.event_type = event_type
        self.data = data
        self.step = step
        self.latency = data.get("latency")

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
        }
        if self.step is not None:
            res["step"] = self.step
        res.update(self.data)
        return res

class Tracer:
    def __init__(self, log_dir: str = "logs/traces"):
        self.log_dir = log_dir
        self.trace_id = self._generate_trace_id()
        self.events: List[TraceEvent] = []
        self.start_time = time.time()
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _generate_trace_id(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        short_id = str(uuid.uuid4())[:8]
        return f"{date_str}-{short_id}"

    def log_event(self, event_type: str, data: Dict[str, Any], step: Optional[int] = None):
        event = TraceEvent(event_type, data, step)
        self.events.append(event)
        
        # Also print to console for immediate visibility (optional, but good for debugging)
        summary = data.get('summary', '')
        print(f"[{event.timestamp}] [Trace:{self.trace_id}] [{event_type}]" + (f" step:{step}" if step is not None else "") + f" - {summary}")
        
        # If there's an error, highlight it
        if "error_code" in data:
            print(f"  ERROR: {data['error_code']} - {data.get('error_message', '')}")

    def log_model_call(self, model: str, prompt_summary: str, response_summary: str, latency: float, step: Optional[int] = None):
        self.log_event("model_call", {
            "summary": "LLM 请求完成",
            "model": model,
            "prompt_summary": prompt_summary,
            "response_summary": response_summary,
            "latency": latency
        }, step=step)

    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], step: Optional[int] = None):
        self.log_event("tool_call", {
            "summary": f"调用工具: {tool_name}",
            "tool": tool_name,
            "arguments": arguments
        }, step=step)

    def log_tool_result(self, tool_name: str, result_summary: str, latency: float, step: Optional[int] = None, error_code: Optional[str] = None):
        data = {
            "summary": f"工具 {tool_name} 执行结束",
            "tool": tool_name,
            "result_summary": result_summary,
            "latency": latency
        }
        if error_code:
            data["error_code"] = error_code
        self.log_event("tool_result", data, step=step)

    def finalize(self, final_result: str):
        total_latency = time.time() - self.start_time
        self.log_event("final_result", {
            "summary": "任务执行完成",
            "final_result": final_result,
            "total_latency": total_latency
        })
        self.save_to_file()

    def save_to_file(self):
        filename = os.path.join(self.log_dir, f"trace_{self.trace_id}.json")
        trace_data = {
            "trace_id": self.trace_id,
            "start_time": datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "events": [e.to_dict() for e in self.events]
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, indent=2, ensure_ascii=False)
        print(f"\n[系统]: Trace 日志已保存至 {filename}")
