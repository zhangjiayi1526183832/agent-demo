"""入口 — CLI 聊天循环"""

from llm import chat
from prompts import get_system_message, list_personas


def main():
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

    # system prompt 始终在 messages[0]
    messages = [get_system_message(persona)]

    print(f"\n当前人格: {persona}")
    print("Chat Agent (输入 /exit 退出, /persona 切换人格)")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ")
        if user_input == "/exit":
            print("再见！")
            break

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
        print(f"[DEBUG] 即将发送 {len(messages)} 条消息")
        reply = chat(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"AI: {reply}")


if __name__ == "__main__":
    main()
