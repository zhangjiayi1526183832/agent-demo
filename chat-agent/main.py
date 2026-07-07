"""入口 — CLI 聊天循环"""

import asyncio
import json
import sys

from llm import achat_stream
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
# Agent Loop — 异步版（Day 进阶二）
# ════════════════════════════════════════════════════════════════

async def agent_loop(messages: list[dict], max_steps: int = 10) -> str:
    """ReAct 循环：异步流式 + 工具并行执行"""
    step = 0
    while step < max_steps:
        step += 1
        log("LOOP", f"=== 第 {step} 轮 ===")
        log("DEBUG", f"即将发送 {len(messages)} 条消息，约 {messages_token_count(messages)} tokens")

        if step == 1:
            sys.stdout.write("AI: ")
            sys.stdout.flush()

        async for event_type, data in achat_stream(messages, tools=TOOL_DEFINITIONS):
            if event_type == "text":
                sys.stdout.write(data)
                sys.stdout.flush()

            elif event_type == "done":
                tool_calls = data.get("tool_calls")

                if tool_calls:
                    sys.stdout.write("\n")
                    sys.stdout.flush()

                    prefix_text = data.get("content") or None

                    # ---- 工具并行执行 ----
                    # 用 asyncio.to_thread 把同步工具放到线程池里并发跑
                    async def run_one(tc, prefix=None):
                        fn = tc["function"]
                        name = fn["name"]
                        args = fn.get("arguments", "{}")
                        if isinstance(args, str):
                            args = json.loads(args)

                        log("TOOL", f"调用: {name}({args})")
                        result = await asyncio.to_thread(execute, name, args)
                        log("TOOL", f"结果: {result}")
                        return tc, name, args, result, prefix

                    # 一次性发出所有工具调用，并发执行
                    tasks = [
                        run_one(tc, prefix_text if i == 0 else None)
                        for i, tc in enumerate(tool_calls)
                    ]
                    results = await asyncio.gather(*tasks)

                    # 按顺序追加到 messages
                    for tc, name, args, result, prefix in results:
                        messages.append({
                            "role": "assistant",
                            "content": prefix,
                            "tool_calls": [{
                                "id": tc.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(args) if isinstance(args, dict) else args,
                                },
                            }],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "content": result,
                        })
                    break

                # 最终文本回复
                reply = data.get("content", "")
                messages.append({"role": "assistant", "content": reply})
                sys.stdout.write("\n")
                sys.stdout.flush()
                return reply

    return "(达到最大循环步数，已中止)"


# ════════════════════════════════════════════════════════════════

async def main():
    global DEBUG

    personas = list_personas()
    print("可用人格:")
    for i, name in enumerate(personas):
        print(f"  [{i}] {name}")
    choice = input("选择人格编号 (默认 0): ").strip()
    try:
        persona = personas[int(choice)]
    except (ValueError, IndexError):
        persona = personas[0]

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
                # 清除旧历史——旧人格的对话风格会污染新人格
                messages = [get_system_message(persona)]
                save_history(messages)
                print(f"已切换为: {persona}（对话历史已重置）")
            except (ValueError, IndexError):
                print("无效选择")
            continue

        messages.append({"role": "user", "content": user_input})

        before = len(messages)
        messages = trim_context(messages, max_tokens=8000)
        if len(messages) < before:
            log("MEMORY", f"上下文裁剪: {before} → {len(messages)} 条消息")

        await agent_loop(messages)
        save_history(messages)


if __name__ == "__main__":
    asyncio.run(main())
