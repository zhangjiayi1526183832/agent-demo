"""结构化日志 — 给 Agent 的"黑匣子" """

import time
import json

# ---- 全局日志开关 ----
ENABLED = False


# ---- 单次 Agent 运行的追踪记录 ----

class Trace:
    """收集一次 agent_loop 调用的所有事件，运行结束后打印摘要"""

    def __init__(self):
        self.events = []
        self.start_time = time.time()
        self.token_count = {"input": 0, "output": 0}
        self.tool_count = 0

    def event(self, category: str, detail: str, **kwargs):
        """记录一个事件"""
        if not ENABLED:
            return
        ts = time.time() - self.start_time
        entry = {
            "ts": round(ts, 3),
            "category": category,
            "detail": detail,
            **kwargs,
        }
        self.events.append(entry)

        # 实时终端输出
        tag = category.upper()
        print(f"[+{entry['ts']:>6.3f}s] [{tag}] {detail}")

    def add_tokens(self, input_tokens: int, output_tokens: int = 0):
        self.token_count["input"] += input_tokens
        self.token_count["output"] += output_tokens

    def add_tool_call(self):
        self.tool_count += 1

    def summary(self) -> dict:
        """打印并返回摘要"""
        elapsed = time.time() - self.start_time
        info = {
            "耗时": f"{elapsed:.2f}s",
            "事件数": len(self.events),
            "LLM调用轮数": sum(1 for e in self.events if e["category"] == "llm"),
            "工具调用次数": self.tool_count,
        }
        if ENABLED and self.events:
            print(f"\n{'─'*40}")
            print("运行摘要:")
            for k, v in info.items():
                print(f"  {k}: {v}")
            print(f"{'─'*40}")
        return info

    def save(self, filepath: str = "trace.json"):
        """保存追踪记录到文件"""
        if not ENABLED:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "events": self.events,
                "token_count": self.token_count,
                "tool_count": self.tool_count,
                "elapsed": time.time() - self.start_time,
            }, f, indent=2, ensure_ascii=False)
