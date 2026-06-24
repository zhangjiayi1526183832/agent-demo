"""记忆管理 — 聊天历史的持久化与上下文窗口管理"""

import json
import os

HISTORY_FILE = "history.json"

# ---- Token 估算（粗略：1 个中文字 ≈ 2 tokens，1 个英文词 ≈ 1.3 tokens）----

def count_tokens(text: str) -> int:
    """粗略估算 token 数（非精确，不需要 tiktoken 库）"""
    count = 0
    for ch in text:
        if '一' <= ch <= '鿿':
            count += 2       # 中文字符 ~2 tokens
        else:
            count += 1
    return count // 4 + 1   # 平均每 token ≈ 4 个字符


def messages_token_count(messages: list[dict]) -> int:
    """估算整个 messages 列表的 token 数"""
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, str):
            total += count_tokens(content)
        # tool_calls 也占 token
        if m.get("tool_calls"):
            total += count_tokens(json.dumps(m["tool_calls"], ensure_ascii=False))
    return total


# ---- 上下文窗口裁剪 ----

def trim_context(messages: list[dict], max_tokens: int = 8000) -> list[dict]:
    """保留 system prompt + 最近的对话，超出部分从中间截断

    规则：
    - messages[0] 是 system prompt，永远保留
    - 按消息对（user + assistant + tool）从后往前保留
    - 估算 token 数，超出 max_tokens 就从前面开始丢
    """
    if len(messages) <= 1:
        return messages

    system_msg = messages[0]
    history = messages[1:]

    # 从后往前取，直到接近上限
    kept = []
    current_tokens = count_tokens(system_msg.get("content", ""))

    for m in reversed(history):
        content = m.get("content") or ""
        t = count_tokens(content) if isinstance(content, str) else 0
        if m.get("tool_calls"):
            t += count_tokens(json.dumps(m["tool_calls"], ensure_ascii=False))
        if current_tokens + t > max_tokens:
            break
        kept.insert(0, m)
        current_tokens += t

    return [system_msg] + kept


# ---- 持久化 ----

def save_history(messages: list[dict], filepath: str = HISTORY_FILE):
    """保存 messages 到 JSON 文件（跳过 system prompt）"""
    # 不保存 system prompt——因为每次启动会重新设置
    to_save = [m for m in messages if m.get("role") != "system"]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)


def load_history(filepath: str = HISTORY_FILE) -> list[dict]:
    """从 JSON 文件加载历史消息"""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, IOError):
        pass
    return []
