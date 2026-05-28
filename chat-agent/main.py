"""入口 — CLI 聊天循环"""

from llm import chat


def main():
    messages = []  # 对话历史：每次请求都带上全部历史

    print("Chat Agent (输入 /exit 退出)")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ")
        if user_input == "/exit":
            print("再见！")
            break

        messages.append({"role": "user", "content": user_input})
        print(f"[DEBUG] 即将发送 {len(messages)} 条消息")  # 观察上下文增长
        reply = chat(messages)  # 把整个历史发过去
        messages.append({"role": "assistant", "content": reply})
        print(f"AI: {reply}")


if __name__ == "__main__":
    main()
