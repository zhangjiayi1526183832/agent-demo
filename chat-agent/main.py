"""入口 — CLI 聊天循环"""

import json

from llm import chat
from prompts import get_system_message, list_personas
from tools import TOOL_DEFINITIONS, execute
from memory import (
    save_history, load_history,
    trim_context, messages_token_count,
)

# ---- 日志开关 ----
DEBUG = False

def log(tag: str, msg: str):
    if DEBUG:
        print(f"[{tag}] {msg}")


# ════════════════════════════════════════════════════════════════
# Agent Loop（Day 5）
# ════════════════════════════════════════════════════════════════

def agent_loop(messages: list[dict], max_steps: int = 10) -> str:
    step = 0
    while step < max_steps:
        step += 1
        log("LOOP", f"=== 第 {step} 轮 ===")
        log("DEBUG", f"即将发送 {len(messages)} 条消息，约 {messages_token_count(messages)} tokens")

        response = chat(messages, tools=TOOL_DEFINITIONS)
        tool_calls = response.get("tool_calls")

        if tool_calls:
            for tc in tool_calls:
                fn = tc["function"]
                name = fn["name"]
                args = fn.get("arguments", "{}")
                if isinstance(args, str):
                    args = json.loads(args)

                log("TOOL", f"调用: {name}({args})")
                result = execute(name, args)
                log("TOOL", f"结果: {result}")

                messages.append({
                    "role": "assistant", "content": None,
                    "tool_calls": [tc],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
            continue

        reply = response.get("content", "")
        messages.append({"role": "assistant", "content": reply})
        return reply

    return "(达到最大循环步数，已中止)"


# ════════════════════════════════════════════════════════════════

def main():
    global DEBUG

    # 选择人格
    personas = list_personas()
    print("可用人格:")
    for i, name in enumerate(personas):
        print(f"  [{i}] {name}")
    choice = input("选择人格编号 (默认 0): ").strip()
    try:
        persona = personas[int(choice)]
    except (ValueError, IndexError):
        persona = personas[0]

    # ---- Day 6: 加载历史对话 ----
    history = load_history()
    messages = [get_system_message(persona)] + history
    if history:
        print(f"已加载 {len(history)} 条历史消息")

    print(f"\n当前人格: {persona}")
    print("Chat Agent (输入 /exit 退出, /persona 切换人格, /debug 切换日志, /clear 清除记忆)")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ")
        if user_input == "/exit":
            save_history(messages)
            print("记忆已保存，再见！")
            break
        if user_input == "/debug":
            DEBUG = not DEBUG
            print(f"日志已{'开启' if DEBUG else '关闭'}")
            continue
        if user_input == "/clear":
            # 清除所有历史，只保留 system prompt
            messages = [messages[0]]
            save_history(messages)
            print("记忆已清除")
            continue
        if user_input == "/persona":
            print("可用人格:")
            for i, name in enumerate(personas):
                print(f"  [{i}] {name}")
            choice = input("切换人格编号: ").strip()
            try:
                persona = personas[int(choice)]
                messages[0] = get_system_message(persona)
                print(f"已切换为: {persona}")
            except (ValueError, IndexError):
                print("无效选择")
            continue

        messages.append({"role": "user", "content": user_input})

        # ---- Day 6: 上下文裁剪，防止无限增长 ----
        before = len(messages)
        messages = trim_context(messages, max_tokens=8000)
        if len(messages) < before:
            log("MEMORY", f"上下文裁剪: {before} → {len(messages)} 条消息")

        reply = agent_loop(messages)
        print(f"AI: {reply}")

        # ---- Day 6: 每次对话后保存 ----
        save_history(messages)


if __name__ == "__main__":
    main()
