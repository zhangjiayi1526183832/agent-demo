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

## Day 4：Tool Calling（工具调用）（2026-05-29）

### 实现了什么

三个文件全部改动：

**tools.py** — 定义 4 个工具 + 执行函数：

```python
# 工具定义（JSON Schema，告诉 LLM 工具怎么用）
TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "get_current_time", ...}},
    {"type": "function", "function": {"name": "get_weather", ...}},
    {"type": "function", "function": {"name": "calculate", ...}},
    {"type": "function", "function": {"name": "run_shell", ...}},
]

# 执行函数（真正干活的地方）
def execute(name, arguments):
    if name == "get_current_time": return datetime.now()
    if name == "calculate": return eval(expression)
    ...
```

**llm.py** — 返回完整消息对象，不再只是文本：

```python
# Day 3: 只返回 str
return data["choices"][0]["message"]["content"]

# Day 4: 返回完整 dict（可能包含 tool_calls）
return {
    "role": "assistant",
    "content": msg.get("content"),       # 普通文本回复时为 str
    "tool_calls": msg.get("tool_calls"), # 想调工具时为 list
}
```

**main.py** — 加入工具调用内循环：

```python
messages.append({"role": "user", "content": user_input})

while True:  # 内循环：工具调用
    response = chat(messages, tools=TOOL_DEFINITIONS)

    if response["tool_calls"]:
        for tc in response["tool_calls"]:
            result = execute(tc["function"]["name"], args)
            messages.append({"role": "tool", "content": result, ...})
        continue  # 继续循环，LLM 看到结果后再决定

    # 纯文本回复，退出内循环
    print(response["content"])
    break
```

### 现在能做什么

实测四个工具全部生效：

```
You: 现在几点？
[TOOL] 调用: get_current_time({})
[TOOL] 结果: 2026-05-29 10:43:45
AI: 现在是 2026年5月29日 10:43:45。

You: 123 * 456 + 789
[TOOL] 调用: calculate({'expression': '123*456+789'})
[TOOL] 结果: 56877
AI: 计算结果是 56,877。

You: 北京天气怎么样？
[TOOL] 调用: get_weather({'city': '北京'})
[TOOL] 结果: 晴，25°C，湿度 40%
AI: ☀️ 天气晴，温度25°C，湿度40%...

You: ls 一下当前目录
[TOOL] 调用: run_shell({'command': 'ls -la'})
[TOOL] 结果: (真实文件列表)
AI: (列出了目录中的所有文件)
```

甚至能**链式调用**——LLM 调一个工具后不满意，自动调下一个：

```
You: 北京天气怎么样？
[TOOL] get_weather('北京') → "暂无数据"  ← 第一次失败
[TOOL] get_current_time() → "10:44"     ← 自动补调时间
AI: 虽然没拿到天气，但现在时间是...     ← 给出有用回答
```

### 不足在哪里（痛点）

**1. LLM 是"被动的"——不会主动行动**

每次都需要用户先输入。LLM 不会主动说"我注意到天气变了，需要提醒你"。它等待用户触发。

**2. 工具调用质量不稳定**

LLM 有时选错工具，有时传错参数。工具定义（description）的质量直接决定 LLM 的调用准确率。

**3. 没有判断标准——调用完就结束了**

LLM 不会验证工具结果是否符合预期。比如计算 1/0 会返回 "计算错误"，但 LLM 不会重试或调整策略。

**4. 最关键的问题：这还不是真正的 Agent**

当前的循环是这样的：

```
用户输入 → LLM思考 → 调用工具 → LLM总结 → 结束
```

而真正的 Agent 循环应该是：

```
用户输入 → LLM思考 → 调用工具 → 观察结果 → 
LLM再思考 → 再调用工具 → 再观察 → ... → 
LLM判断"任务完成" → 结束
```

现在的代码里，内循环 `while True` 已经能支持多次工具调用，但它本质上是**反应式的**——LLM 只会"被要求回答一个问题"。它不会自主决定"我需要完成一个多步任务"。

### 如何触发这个不足

```
You: 帮我查一下北京和上海的天气，告诉我哪个城市更热
```

预期行为：LLM 并行/串行查两个城市 → 比较温度 → 回答
实际可能：LLM 只查一个城市就回答了，或者调用顺序混乱

```
You: 创建一个 test 目录，在里面新建一个 readme.txt，写入 "hello"
```

这是一个需要 3 步的任务：mkdir → cd → write file。当前 Agent 很难自主规划并执行这种多步任务。

### 为什么

当前的循环设计是"一问一答"的扩展：

```python
while True:  # 外层：每轮用户输入
    user_input = input()
    messages.append(user_input)
    
    while True:  # 内层：处理当前这一个问题
        response = chat(messages, tools)
        if tool_calls: ...  # 执行工具
        else: break         # 回答完毕，等待下一个用户输入
```

问题在于：**外层循环等待用户输入，内层循环不知道自己"做完了没有"。**

真正的 Agent 不需要等待用户输入就能自主推进任务。它需要自己决定"下一步做什么"。

### 引出什么概念

**Agent Loop**——Day 5 的主题。把上面的逻辑翻转：

```python
while True:
    response = chat(messages, tools)
    
    if task_complete:
        break
    elif tool_calls:
        execute()
        observe()
    else:
        # LLM 在"思考"，等待它做出决定
        ...
```

关键变化：**循环不再由用户输入驱动，而是由 LLM 的"思考-行动-观察"循环驱动。**

这就是 ReAct 模式（Reasoning + Acting）：
```
Thought → Action → Observation → Thought → Action → ...
```

### 核心理解

LLM 的输出不再是单一的文本回复，而是两种类型交替出现：

| 类型 | 含义 | 谁执行 |
|------|------|--------|
| `content: "..."` | 对用户说话 | LLM |
| `tool_calls: [...]` | 要执行的动作 | **你的代码** |

Agent 的本质就是协调这两种输出。

---

## Day 5：Agent Loop（2026-06-23）

### 实现了什么

**把埋在 main() 里的内循环提取为有名字的函数——`agent_loop()`。**

之前（Day 4）的 main.py：

```python
while True:  # 外层等用户输入
    user_input = input()
    messages.append(...)
    
    while True:  # 内层工具调用 — 匿名的，隐藏的
        response = chat(messages, tools)
        if tool_calls: ...
        else: break
```

现在（Day 5）：

```python
# agent_loop 是独立函数，有名字、有参数、有返回
def agent_loop(messages, max_steps=10) -> str:
    step = 0
    while step < max_steps:
        step += 1
        response = chat(messages, tools=TOOL_DEFINITIONS)
        
        if response["tool_calls"]:
            for tc in tool_calls:           # Action
                execute(name, args)
                messages.append(result)     # Observation
            continue                        # 下一轮 Thought
        
        return response["content"]          # 任务完成


# main() 变成薄薄一层：处理用户输入，交给 Agent Loop
def main():
    messages = [...]
    while True:
        user_input = input()
        messages.append(user_input)
        reply = agent_loop(messages)       # ← 整个 Agent 逻辑在这里
        print(reply)
```

### 为什么这个改动是 Day 5 的核心

不是加了新功能，而是**给了一个已经存在的东西名字**。

Day 4 的代码已经能多步工具调用——但内循环是埋在 main() 里的，看起来像是个"实现细节"。提取出来之后你才会意识到：

**这个循环本身就是 Agent。** 剩下的东西——用户输入、打印输出——只是外层壳。

### 现在能做什么

开启 `/debug`，能看到 ReAct 循环的每一轮：

```
[LOOP] === 第 1 轮 ===             ← Thought: LLM 分析任务
[DEBUG] 即将发送 6 条消息
[TOOL] 调用: get_weather('北京')   ← Action: 执行工具
[TOOL] 结果: 晴，25°C
[TOOL] 调用: get_weather('上海')   ← Action: 并行执行
[TOOL] 结果: 多云，28°C
                                    ← Observation: 结果追加到上下文
[LOOP] === 第 2 轮 ===             ← Thought: LLM 看到结果
AI: 上海(28°C)比北京(25°C)更热    ← 最终回复
```

一次用户输入，触发了两轮 LLM 调用，LLM 自己规划了一轮要两个天气数据。

### 为什么所有 Agent 本质上都是这个循环

| Agent 产品 | 区别在哪 | 共同之处 |
|------------|---------|----------|
| 你的 Agent | 4 个工具（时间/天气/计算/shell） | `agent_loop()` |
| Claude Code | 大量工具（读写文件/执行命令/搜索） | `agent_loop()` |
| Cursor | 代码编辑工具 | `agent_loop()` |
| OpenHands | Docker 沙箱 + 浏览器 | `agent_loop()` |

**区别只是工具列表不同 + prompt 不同。核心循环结构完全一样。**

### ReAct 模式的本质

```
Thought（思考）→  LLM 分析当前状态，决定下一步
  ↓
Action（行动）→  你的代码执行工具
  ↓
Observation（观察）→ 工具结果追加到上下文
  ↓
Thought（思考）→  LLM 看到结果，重新分析，决定下一步
  ↓
... 循环，直到 LLM 决定"完成了"（tool_calls 为 None）
```

`max_steps=10` 是安全阀——防止 LLM 陷入死循环。

### 不足在哪里（痛点）

**1. 上下文无限增长（Day 2 痛点 B 的回旋镖）**

每轮 Agent Loop 都在 messages 里追加 2 条以上消息（tool_call + tool result）。多步任务很快积累几十条。再加上 Day 2 的多轮对话记忆（每次用户输入也追加），这个列表**只增不减**。

**2. 对话结束后记忆全部丢失**

程序关闭 → messages 列表消失 → 下次启动 AI 完全不记得你。目前 `history.json` 写了但没用。

**3. 没有错误恢复**

`agent_loop` 里如果工具执行报错，只是追加一条错误信息到上下文。但 LLM 可能反复尝试同一个错误工具，直到 `max_steps` 耗尽。

**4. 没有能力判断"够了"**

`max_steps` 是硬上限，LLM 自己不会说"我试了 3 次都失败，换个思路吧"。它在上下文满了之前会一直试。

### 如何触发这些不足

```bash
You: 帮我创建项目目录结构
# → LLM 可能调很多次 run_shell，每次都追加消息
# → messages 从 5 条快速涨到 30+ 条

# 然后关掉程序重开：
python main.py
You: 我刚才让你建了什么？
# → AI：？？？完全不记得
```

### 引出什么概念

**记忆与状态管理**——Day 6 的主题。

- 上下文太长怎么办？→ 截断、摘要、滑动窗口
- 对话记忆怎么持久化？→ `history.json` 的读写
- token 用完了怎么办？→ context window 的概念

### 核心理解

**Agent ≠ 神秘 AI。Agent = `while True: think(); act(); observe()`**

当你把这个循环提取出来并命名的那一刻，你就已经理解了现代 AI Agent 的工作原理。

---






