"""LLM 调用封装 — 直接用 HTTP 请求调用 API"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """发送 messages 和 tools，返回 assistant message 对象

    返回的 dict 可能包含:
        {"role": "assistant", "content": "文本回复"}
    或:
        {"role": "assistant", "tool_calls": [...], "content": None}
    """
    body = {
        "model": MODEL,
        "messages": messages,
    }
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

    # 标准化返回格式
    return {
        "role": "assistant",
        "content": msg.get("content"),
        "tool_calls": msg.get("tool_calls"),
    }
