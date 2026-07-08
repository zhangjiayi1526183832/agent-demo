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
from logger import Trace
import logger
import rag

# ---- 日志开关（/debug 同时控制旧 DEBUG 和 logger.ENABLED）----
DEBUG = False


# ════════════════════════════════════════════════════════════════
# Agent Loop — 异步版 + 可观测性
# ════════════════════════════════════════════════════════════════

async def agent_loop(messages: list[dict], max_steps: int = 10) -> str:
    """ReAct 循环：异步流式 + 工具并行 + 结构化日志"""
    trace = Trace()
    trace.event("agent_start", f"开始处理，当前 {len(messages)} 条上下文消息")

    step = 0
    while step < max_steps:
        step += 1
        token_est = messages_token_count(messages)
        trace.event("llm", f"第{step}轮API调用 → 消息{len(messages)}条 预估{token_est}tokens")

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

                    async def run_one(tc, prefix=None):
                        fn = tc["function"]
                        name = fn["name"]
                        args = fn.get("arguments", "{}")
                        if isinstance(args, str):
                            args = json.loads(args)

                        trace.event("tool", f"调用: {name}", args=str(args))
                        result = await asyncio.to_thread(execute, name, args)
                        trace.event("tool_result", f"{name} → {result[:50]}")
                        trace.add_tool_call()
                        return tc, name, args, result, prefix

                    tasks = [
                        run_one(tc, prefix_text if i == 0 else None)
                        for i, tc in enumerate(tool_calls)
                    ]
                    results = await asyncio.gather(*tasks)

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

                trace.event("agent_end", f"完成，共{step}轮 {trace.tool_count}次工具调用")
                trace.summary()
                trace.save()
                return reply

    trace.event("agent_end", "达到最大步数，中止")
    trace.summary()
    trace.save()
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
            logger.ENABLED = DEBUG  # 同步开关
            print(f"可观测日志已{'开启' if DEBUG else '关闭'}")
            continue
        if user_input.startswith("/load"):
            filepath = user_input[5:].strip()
            if not filepath:
                print("用法: /load <文件路径>")
                continue
            try:
                n = rag.load_document(filepath)
                print(f"已加载: {filepath} → {n} 个片段\n{rag.status()}")
            except FileNotFoundError:
                print(f"文件不存在: {filepath}")
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
            if logger.ENABLED:
                print(f"[OBSERVE] 上下文裁剪: {before} → {len(messages)} 条消息")

        await agent_loop(messages)
        save_history(messages)


if __name__ == "__main__":
    asyncio.run(main())
