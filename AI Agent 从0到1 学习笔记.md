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
