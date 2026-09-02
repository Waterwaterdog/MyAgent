import os
import sys
import json
import time
import subprocess
import glob

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_agent(task, mode="standard", token_budget=4000):
    cmd = [sys.executable, "-m", "coding_agent.main", task]
    if mode == "plan":
        cmd.append("--plan")
    elif mode == "react":
        cmd.append("--react")
    elif mode == "hybrid":
        cmd.append("--hybrid")
    
    cmd.extend(["--token-budget", str(token_budget)])
    
    print(f"\n>>> Running Task: {task[:50]}...")
    print(f">>> Mode: {mode}, Token Budget: {token_budget}")
    
    start_time = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    stdout, stderr = process.communicate()
    end_time = time.time()
    
    return stdout, stderr, end_time - start_time

def get_latest_trace():
    traces = glob.glob(os.path.join(project_root, "logs", "traces", "*.json"))
    if not traces:
        return None
    return max(traces, key=os.path.getmtime)

def analyze_trace(trace_path):
    with open(trace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get("events", [])
    
    metrics = {
        "success": False,
        "steps": 0,
        "tool_calls": 0,
        "repeated_tool_calls": 0,
        "errors": 0,
        "max_tokens": 0,
        "compression_triggered": False,
        "total_latency": 0
    }
    
    tool_call_history = set()
    
    for event in events:
        e_type = event.get("event_type")
        if e_type == "model_call":
            metrics["steps"] += 1
            # Extract tokens from prompt_summary: "Messages: X, Tokens: Y"
            summary = event.get("prompt_summary", "")
            if "Tokens:" in summary:
                try:
                    tokens = int(summary.split("Tokens:")[1].strip())
                    metrics["max_tokens"] = max(metrics["max_tokens"], tokens)
                except:
                    pass
        elif e_type == "tool_call":
            metrics["tool_calls"] += 1
            tool_info = (event.get("tool"), str(event.get("arguments")))
            if tool_info in tool_call_history:
                metrics["repeated_tool_calls"] += 1
            tool_call_history.add(tool_info)
        elif e_type == "tool_result" and "error_code" in event:
            metrics["errors"] += 1
        elif e_type == "context_compression":
            metrics["compression_triggered"] = True
        elif e_type == "final_result":
            metrics["success"] = "任务执行完成" in event.get("summary", "")
            metrics["total_latency"] = event.get("total_latency", 0)
            
    return metrics

def main():
    # Setup test files
    with open("bench_hello.py", "w") as f:
        f.write("def hello():\n    print('hello world')\n")
    
    tasks = [
        {"name": "BaseTask", "task": "读取 bench_hello.py 的内容并打印出来。", "mode": "standard"},
        {"name": "ErrorRecovery", "task": "读取不存在的文件 'non_existent.txt'，如果报错，请列出当前目录文件。", "mode": "react"},
        {"name": "ParallelRead", "task": "同时读取 bench_hello.py 和 requirements.txt 的内容。", "mode": "standard"},
        {"name": "ComplexHybrid", "task": "分析 bench_hello.py，将其改写为支持接收参数的函数，然后创建一个新的测试文件 bench_test.py 来运行它。", "mode": "hybrid"},
        {"name": "LoopGuard", "task": "反复尝试读取一个明显不存在的文件 'ghost.txt' 5次。", "mode": "standard"},
        {"name": "Compression", "task": "列出项目根目录下的所有文件和文件夹，然后读取其中三个文件的内容，最后总结项目结构。", "mode": "react", "budget": 1000}
    ]
    
    results = []
    
    for t in tasks:
        stdout, stderr, duration = run_agent(t["task"], t["mode"], t.get("budget", 4000))
        trace_path = get_latest_trace()
        if trace_path:
            metrics = analyze_trace(trace_path)
            metrics["name"] = t["name"]
            metrics["mode"] = t["mode"]
            results.append(metrics)
        else:
            print(f"Warning: No trace found for task {t['name']}")

    # Print results table
    print("\n" + "="*80)
    print(f"{'Task Name':<20} | {'Mode':<8} | {'Steps':<5} | {'Tools':<5} | {'Errors':<6} | {'Tokens':<6} | {'Success':<8}")
    print("-"*80)
    for r in results:
        success_str = "YES" if r["success"] else "NO"
        print(f"{r['name']:<20} | {r['mode']:<8} | {r['steps']:<5} | {r['tool_calls']:<5} | {r['errors']:<6} | {r['max_tokens']:<6} | {success_str:<8}")
    print("="*80)

    # Cleanup
    for f in ["bench_hello.py", "bench_test.py"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    main()
