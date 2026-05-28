"""LLM 调用封装 — 直接用 HTTP 请求调用 API"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")


def chat(messages: list[dict]) -> str:
    """发送 messages，返回 AI 的文本回复"""
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
        },
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]
