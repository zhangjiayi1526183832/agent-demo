"""入口 — CLI 聊天循环"""

import json

from llm import chat
from prompts import get_system_message, list_personas
from tools import TOOL_DEFINITIONS, execute

# ---- 日志开关 ----
DEBUG = False

def log(tag: str, msg: str):
    """仅当 DEBUG=True 时打印"""
    if DEBUG:
        print(f"[{tag}] {msg}")


# ════════════════════════════════════════════════════════════════
# Day 5 核心：Agent Loop
# ════════════════════════════════════════════════════════════════

def agent_loop(messages: list[dict], max_steps: int = 10) -> str:
    """Agent 主循环 — LLM 自主决策，循环调用工具，直到任务完成。

    ReAct 模式:
        Thought → Action → Observation → Thought → ...

    返回: LLM 的最终文本回复
    """
    step = 0
    while step < max_steps:
        step += 1
        log("LOOP", f"=== 第 {step} 轮 ===")
        log("DEBUG", f"即将发送 {len(messages)} 条消息")

        response = chat(messages, tools=TOOL_DEFINITIONS)
        tool_calls = response.get("tool_calls")

        if tool_calls:
            # —— Action 阶段 ——
            for tc in tool_calls:
                fn = tc["function"]
                name = fn["name"]
                args = fn.get("arguments", "{}")
                if isinstance(args, str):
                    args = json.loads(args)

                log("TOOL", f"调用: {name}({args})")
                result = execute(name, args)
                log("TOOL", f"结果: {result}")

                # 把工具调用和结果写入上下文
                messages.append({
                    "role": "assistant", "content": None,
                    "tool_calls": [tc],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
            # —— Observation 阶段 ——
            # continue → LLM 看到工具结果，进入下一轮 Thought
            continue

        # —— 最终回复 ——
        # tool_calls 为空 → LLM 认为任务完成
        reply = response.get("content", "")
        messages.append({"role": "assistant", "content": reply})
        return reply

    # 超出最大步数
    return "(达到最大循环步数，已中止)"


# ════════════════════════════════════════════════════════════════

def main():
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

    messages = [get_system_message(persona)]

    print(f"\n当前人格: {persona}")
    print("Chat Agent (输入 /exit 退出, /persona 切换人格, /debug 切换日志)")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ")
        if user_input == "/exit":
            print("再见！")
            break
        if user_input == "/debug":
            DEBUG = not DEBUG
            print(f"日志已{'开启' if DEBUG else '关闭'}")
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

        # 放入用户消息
        messages.append({"role": "user", "content": user_input})

        # 交给 Agent Loop
        reply = agent_loop(messages)
        print(f"AI: {reply}")


if __name__ == "__main__":
    main()
