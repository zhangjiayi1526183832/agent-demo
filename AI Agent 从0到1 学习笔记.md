# AI Agent 从 0 到 1 学习笔记

> 基于《从 0 到 1 手写 AI Chat Agent 学习路线》，以问题驱动的方式记录每一步的学习过程。
> 
> 每完成一天的代码实现后，记录：
> 1. 实现了什么
> 2. 现在能做什么
> 3. 不足在哪里（痛点）
> 4. 如何触发/测试这个不足
> 5. 引出什么新概念
> 6. 如何解决

---

## Day 1：第一个 ChatBot（2026-05-28）

### 实现了什么

两个文件：

- **llm.py** — 封装 HTTP 请求，向 DeepSeek API 发送 `POST /chat/completions`，拿到 AI 回复
- **main.py** — `while True` 循环读取用户输入，调用 `chat()`，打印回复

核心代码极简：

```python
# llm.py — 本质就是一次 HTTP POST
def chat(messages):
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages},
    )
    return response.json()["choices"][0]["message"]["content"]
```

```python
# main.py — 每次对话是独立的
reply = chat([{"role": "user", "content": user_input}])
```

### 现在能做什么

- 单轮问答：用户说一句，AI 回一句
- 每次请求都是**独立**的——AI 会响应任何问题

### 不足在哪里（痛点）

**AI 没有记忆。** 每一轮对话都是全新的。你说过的话，它下一句就忘了。

### 如何触发这个不足

```
You: 我叫 Ezra
AI: 好的，Ezra！

You: 我叫什么？
AI: 抱歉，我不知道你的名字。    ← 已经忘了
```

### 为什么

看代码就明白了——每次调用 `chat()` 只传了**当前这一条**消息：

```python
chat([{"role": "user", "content": "我叫什么？"}])
#     ↑ 只有这一条！没有"我叫 Ezra"的历史
```

LLM 本身**没有任何状态**。它不会记住上次对话。它只知道你这次传给它什么。

### 引出什么概念

**Context（上下文）**——Day 2 的主题。要让 AI "记住"，唯一的办法是把历史消息也一起传过去。

### 解决方案（预告）

把每次对话的消息**追加**到一个列表中，下次请求时把整个列表发过去：

```python
messages = [
    {"role": "user", "content": "我叫 Ezra"},
    {"role": "assistant", "content": "好的，Ezra！"},
    {"role": "user", "content": "我叫什么？"},       # ← 现在 AI 能看到之前的对话了
]
```

这就是 Memory 的本质：**把历史消息重新喂给模型。**

---

## Day 2：Context（上下文）（2026-05-28）

### 实现了什么

只改了三行代码，但概念变化巨大：

```python
# Day 1 — 每次只发当前消息
reply = chat([{"role": "user", "content": user_input}])

# Day 2 — 维护消息列表，每次发全部历史
messages = []
# ...
messages.append({"role": "user", "content": user_input})
reply = chat(messages)                           # ← 把整个历史发过去
messages.append({"role": "assistant", "content": reply})
```

加了 `[DEBUG]` 输出，可以看到每次请求发了几条消息。

### 现在能做什么

- **多轮对话**：AI 能记住之前说过的话
- 实测：先说"我叫Ezra"，再问"我叫什么？"——AI 记住了

### 不足在哪里（痛点）— 有两个

#### 痛点 A：AI 行为不可控

AI 没有固定的"人格"。它可以是任何东西：有时热情，有时冷淡，完全取决于模型自身的随机性。你没办法让它**始终**以某种方式行事。

```
You: 你好
AI: 嗨！今天怎么样？（可能是任何风格）
```

#### 痛点 B：上下文无限增长（更隐蔽但更重要）

观察 `[DEBUG]` 输出：

```
第1轮: [DEBUG] 即将发送 1 条消息
第2轮: [DEBUG] 即将发送 3 条消息
第3轮: [DEBUG] 即将发送 5 条消息
第4轮: [DEBUG] 即将发送 7 条消息  ← 每次都在涨！
```

每轮对话，消息数 +2（user + assistant）。聊 50 轮就是 100 条消息。这意味着：

1. **费用递增**：每轮发送的 token 越来越多，API 费用越来越高
2. **速度递减**：请求体越来越大，响应越来越慢
3. **终将溢出**：模型有上下文窗口上限（如 128K tokens），超过就会报错或截断
4. **早期信息被稀释**：越靠前的对话在大量历史中越难被模型关注到

### 如何触发这两个不足

**触发 A**：
```
You: 你是什么风格？
AI: （每次回答风格可能不同，没有一致性）
```

**触发 B**：
```
# 连续聊 10 轮，观察 [DEBUG] 输出
第1轮: 1 条
第2轮: 3 条
第3轮: 5 条
...
第10轮: 19 条 ← 一直在涨，永远不会减少
```

本质问题：`messages` 列表**只增不减**，没有任何管理策略。

### 为什么

```python
# 当前逻辑
while True:
    messages.append(user_msg)   # 只追加
    chat(messages)              # 全部发送
    messages.append(ai_msg)     # 只追加
#   ↑ 没有任何删除/压缩/截断逻辑
```

### 引出什么概念

- **痛点 A → Day 3：System Prompt**。给 AI 一个固定的"角色"和"行为规则"，约束它的输出风格。
- **痛点 B → Day 6：记忆与状态管理**。上下文不能无限增长，需要策略：截断、摘要、滑动窗口、token 计数。今天先意识到这个问题，后续解决。

### 解决方案（预告）

**System Prompt（Day 3）**：在 messages 最前面加一条 `role: "system"` 的消息：

```python
messages = [
    {"role": "system", "content": "你是一个冷静的 Linux 专家。"},
    {"role": "user", "content": "你好"},
    ...
]
```

system 消息不会被 AI "忘记"（始终在第一条），它定义了 AI 的全局行为规则。

---

## Day 3：System Prompt（人格与规则）（2026-05-28）

### 实现了什么

**prompts.py** — 定义了 5 种人格模板，本质就是一段描述文字：

```python
PERSONAS = {
    "linux_expert": "你是一个冷静的 Linux 专家。回答简洁专业...",
    "catgirl": "你是一只猫娘。每句话结尾都要加'喵~'...",
    ...
}
```

**main.py** — 在 `messages` 列表头部插入 system 消息，且始终保持在 `[0]` 位置：

```python
messages = [{"role": "system", "content": PERSONAS["linux_expert"]}]
#          ↑ 始终在第一条，不会被移除

while True:
    messages.append({"role": "user", "content": user_input})
    reply = chat(messages)   # system + 全部历史 一起发送
    messages.append({"role": "assistant", "content": reply})
```

支持运行时 `/persona` 切换人格。

### 现在能做什么

- AI 有**一致的**行为风格，不会每次回答随机变化
- 可以切换不同人格：猫娘、Linux 专家、面试官、网络工程师
- 实测效果：同样的"你好"，interviewer 说"严肃敲桌子"，catgirl 说"主人～喵~"

### 不足在哪里（痛点）

**AI 只能「说」不能「做」。** 它被关在对话里。

一个 Linux 专家人格的 AI，你问它"现在几点"，它只能编一个时间，不能真的去查询。你让它"执行 ls 命令"，它只能假装输出，不能真的执行。

```
You: 执行 ls /tmp
AI: （Linux 专家人格）
    我会建议你运行：ls -la /tmp
    但很遗憾，我无法在你的系统上真正执行这个命令。
```

它是**纯文本引擎**，没有能力与外部世界交互。

### 如何触发这个不足

```bash
# 选择 linux_expert 人格
You: 现在几点？
AI: （它只能编造或拒绝，无法查询真实时间）

You: 帮我算一下 123 * 456
AI: （它可能算对也可能算错，因为它只是在"预测文本"，
     不是在"执行计算"）

You: 在我的电脑上创建一个 test.txt 文件
AI: （完全做不到——它被隔离在对话里）
```

### 为什么

LLM 的 API 只做一件事：

```python
# LLM 的本质
输入: 一段文本（messages）
输出: 一段文本（assistant reply）
```

它**不会执行动作**。它只会**生成文本**。不管 system prompt 写得多好，都无法突破这个限制。

### 引出什么概念

**Tool Calling（工具调用）**——Day 4 的主题。

让 AI 能"使用工具"的核心思路：

1. 告诉 LLM 有哪些工具可用（tool definitions）
2. LLM 决定"我要用哪个工具"并输出调用指令
3. **你的代码**去真正执行这个工具
4. 把执行结果喂回给 LLM

```
用户: "现在几点？"
  ↓
LLM 输出: {"tool": "get_current_time"}    ← LLM 只生成"意图"
  ↓
你的代码: get_current_time() → "14:30"    ← 代码真正执行
  ↓
LLM 收到结果: "现在是 14:30"              ← LLM 把结果转成自然语言
```

关键理解：**LLM 不会执行动作，它只会生成动作。**

### 解决方案（预告）

在请求中增加 `tools` 参数，告诉 API 有哪些工具。当 LLM 返回 tool_call 时，代码执行工具，结果追加到 messages 中，再次调用 LLM。

---


