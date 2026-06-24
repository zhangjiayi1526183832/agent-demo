"""LLM 调用封装 — 直接用 HTTP 请求调用 API"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """常规模式：一次性返回完整回复"""
    body = {"model": MODEL, "messages": messages}
    if tools:
        body["tools"] = tools

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    data = response.json()
    msg = data["choices"][0]["message"]

    return {
        "role": "assistant",
        "content": msg.get("content"),
        "tool_calls": msg.get("tool_calls"),
    }


# ════════════════════════════════════════════════════════════════
# Streaming（流式输出）
# ════════════════════════════════════════════════════════════════

def chat_stream(messages: list[dict], tools: list[dict] | None = None):
    """流式模式：逐 token 返回，同时累积完整消息用于 tool_calls 检测

    用法:
        for event_type, data in chat_stream(messages, tools):
            if event_type == "text":
                print(data, end="", flush=True)   # 逐字打印
            elif event_type == "done":
                final_message = data               # 完整的 assistant message
    """
    body = {"model": MODEL, "messages": messages, "stream": True}
    if tools:
        body["tools"] = tools

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        stream=True,  # ← 关键：HTTP 层流式读取
    )

    # 累积变量——因为流式模式中 tool_calls 可能分多个 chunk 到达
    accumulated_content = ""
    accumulated_tool_calls = {}  # index → {id, name, arguments_str}

    for line in response.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8")

        # SSE 格式: "data: <json>"
        if not line_str.startswith("data: "):
            continue
        data_str = line_str[6:]  # 去掉 "data: " 前缀
        if data_str == "[DONE]":
            break

        try:
            chunk = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        delta = chunk["choices"][0].get("delta", {})

        # ---- 文本内容 ----
        if "content" in delta and delta["content"]:
            accumulated_content += delta["content"]
            yield ("text", delta["content"])

        # ---- 工具调用（可能分多个 chunk）----
        if "tool_calls" in delta:
            for tc in delta["tool_calls"]:
                idx = tc.get("index", 0)
                if idx not in accumulated_tool_calls:
                    accumulated_tool_calls[idx] = {
                        "id": tc.get("id", ""),
                        "function": {"name": "", "arguments": ""},
                    }
                entry = accumulated_tool_calls[idx]
                if "id" in tc:
                    entry["id"] = tc["id"]
                if "function" in tc:
                    if "name" in tc["function"] and tc["function"]["name"]:
                        entry["function"]["name"] += tc["function"]["name"]
                    if "arguments" in tc["function"]:
                        entry["function"]["arguments"] += tc["function"]["arguments"]

    # ---- 构建最终消息 ----
    final_tool_calls = None
    if accumulated_tool_calls:
        final_tool_calls = [
            {"index": idx, "type": "function", **entry}
            for idx, entry in accumulated_tool_calls.items()
        ]

    yield ("done", {
        "role": "assistant",
        "content": accumulated_content or None,
        "tool_calls": final_tool_calls,
    })
