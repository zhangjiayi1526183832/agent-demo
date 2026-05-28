# 从 0 到 1 手写 AI Chat Agent 学习路线（聊天机器人版）

> 目标：
> 
> 不依赖任何 AI Agent 框架，
> 从底层亲手实现一个类似 ChatGPT 的聊天 Agent。
> 
> 学习重点：
> 
> - LLM 如何工作
> 
> - Prompt 是什么
> 
> - Context 如何管理
> 
> - Memory 如何实现
> 
> - Agent Loop 如何运行
> 
> - Tool Calling 的本质
> 
> 最终目标：
> 
> 自己实现一个：
> 
> ```Plain Text
> 能聊天
> 能记忆上下文
> 能调用工具
> 能自主循环思考
> ```
> 
> 的 AI Chat Agent。
> 
> 

---

# 一、为什么先做聊天 Agent

这是最正确的起点。

因为：

```Plain Text
聊天 Agent
=
所有 AI Agent 的基础
```

包括：

- Claude Code

- Cursor

- OpenHands

- Manus

本质上：

都只是：

```Plain Text
聊天 + Tool Calling + Loop
```

---

# 二、学习原则（非常重要）

## 不要先学框架

暂时不要碰：

- LangChain

- CrewAI

- AutoGen

- LangGraph

原因：

框架会隐藏：

- Context 管理

- Prompt

- Tool Calling

- Runtime

- Loop

你会：

```Plain Text
会调框架
但不理解 Agent 原理
```

---

## 每天代码不要超过 300 行

当前阶段：

目标是：

```Plain Text
理解原理
```

不是：

```Plain Text
做产品
```

---

## 先做 CLI 聊天机器人

不要一开始做：

- Web UI

- Electron

- 微信机器人

- 语音助手

因为：

UI 会干扰核心学习。

---

# 三、最终你会真正理解什么

学习结束后，你会真正理解：

---

## ChatGPT 本质是什么

本质：

```Plain Text
LLM + Context
```

---

## Agent 本质是什么

本质：

```Plain Text
LLM + Tool + Loop
```

---

## Memory 本质是什么

本质：

```Plain Text
重新喂回历史消息
```

---

## Prompt 本质是什么

本质：

```Plain Text
运行时规则
```

---

## 为什么 Agent 能“思考”

因为：

```Plain Text
Thought
→ Action
→ Observation
→ Thought
```

循环。

---

# 四、7 天学习路线（聊天 Agent 版）

---

# Day 1：你的第一个 AI ChatBot

## 今日目标

实现：

```Plain Text
用户输入
↓
调用 OpenAI API
↓
AI 回复
```

---

## 今天重点

理解：

```Plain Text
LLM API 是怎么工作的
```

---

## 今日学习内容

### OpenAI Chat Completion API

重点：

- model

- messages

- system prompt

- user prompt

---

## 今日必须实现

CLI 聊天：

```Bash
You: hello
AI: hi
```

---

## 今日重点理解

### ChatGPT 本质：

```Plain Text
输入 messages
输出 assistant message
```

---

# Day 2：上下文（Context）是什么

# 这是最重要的一天之一。

因为：

你会第一次理解：

```Plain Text
LLM 没有真正记忆
```

---

## 今日目标

实现：

```Python
messages.append(...)
```

---

## 让 AI 记住：

```Plain Text
前面的聊天内容
```

---

## 今日必须实现

例如：

```Plain Text
You: 我叫 Ezra
AI: 好的

You: 我叫什么？
AI: 你叫 Ezra
```

---

## 今日重点理解

Memory 本质：

```Plain Text
把历史消息重新发给模型
```

---

# Day 3：System Prompt（人格与规则）

## 今日目标

让 AI：

```Plain Text
拥有固定行为模式
```

---

## 今日学习内容

### System Prompt

例如：

```Plain Text
你是一个冷静的 Linux 专家。
```

---

## 今日必须实现

例如：

```Plain Text
不同人格：
- 猫娘
- Linux 专家
- 面试官
- 网络工程师
```

---

## 今日重点理解

Prompt 本质：

```Plain Text
运行时规则
```

而不是：

```Plain Text
提问技巧
```

---

# Day 4：Tool Calling（真正进入 Agent）

# 从今天开始：

# ChatBot 开始变成 Agent。

---

## 今日目标

让 AI：

```Plain Text
决定调用哪个工具
```

---

## 推荐实现工具

简单即可：

- time

- weather（假数据）

- calculator

- shell

---

## 示例

用户：

```Plain Text
现在几点
```

AI：

```JSON
{
  "tool": "time"
}
```

Python：

```Python
get_current_time()
```

---

## 今日重点理解

LLM：

```Plain Text
不会执行动作
```

它只会：

```Plain Text
生成动作
```

---

# Day 5：Agent Loop（核心）

# 这是整个学习路线最重要的一天。

---

## 今日目标

实现：

```Python
while True:
```

循环。

---

## 今日必须实现

```Python
while True:
    response = llm(messages)

    if tool_call:
        run_tool()
        append_result()
    else:
        break
```

---

## 今日重点理解

现代所有 Agent：

- Claude Code

- Cursor

- OpenHands

本质都是：

```Python
loop()
```

---

# Day 6：记忆与状态管理

## 今日目标

让 AI：

```Plain Text
长期保存信息
```

---

## 推荐实现

### 保存聊天记录

例如：

```JSON
history.json
```

---

## 今日学习内容

- 短期记忆

- 长期记忆

- context window

- token limit

---

## 今日重点理解

真正的“记忆”：

不是模型。

而是：

```Plain Text
状态管理
```

---

# Day 7：完整 Chat Agent

# 最终项目：

# 你自己的 ChatGPT Mini

---

## 功能目标

支持：

### 多轮聊天

例如：

```Plain Text
记住上下文
```

---

### System Prompt

例如：

```Plain Text
切换人格
```

---

### Tool Calling

例如：

```Plain Text
获取时间
计算
执行 shell
```

---

### Agent Loop

例如：

```Plain Text
自动连续调用工具
```

---

### 长期记忆

例如：

```Plain Text
保存历史聊天
```

---

# 五、推荐项目结构（极简）

```Plain Text
chat-agent/
│
├── main.py
├── llm.py
├── tools.py
├── memory.py
├── prompts.py
└── history.json
```

---

# 六、推荐技术栈（极简版）

## Python

必须掌握：

- requests

- json

- subprocess

- asyncio（后面学）

---

## API

理解：

- HTTP

- REST

- API Key

- JSON

---

## OpenAI API

重点：

- Chat Completion

- Messages

- Structured Output

- Tool Calling

---

# 七、现阶段不要学习的东西

暂时不要深入：

- LangChain

- Multi\-Agent

- RAG

- Vector DB

- MCP

- Browser Agent

原因：

```Plain Text
先理解最小 Agent
再学习复杂系统
```

---

# 八、推荐阅读（真正重要）

## ReAct

重点理解：

```Plain Text
Thought
→ Action
→ Observation
```

---

## Function Calling

重点：

- JSON Schema

- Tool Description

- Structured Output

---

# 九、你学习结束后会真正理解什么

你会发现：

---

## ChatGPT 本质：

```Plain Text
LLM + Context
```

---

## AI Agent 本质：

```Python
while True:
    think()
    act()
    observe()
```

---

## 所谓“记忆”：

只是：

```Plain Text
重新喂回上下文
```

---

## 所谓“思考”：

只是：

```Plain Text
生成下一步 token
```

---

# 十、下一阶段学习路线（完成后）

当你真正理解：

- Context

- Prompt

- Tool Calling

- Loop

- State

之后再进入：

---

## 第一阶段

- LangGraph

- MCP

- Async Agent

---

## 第二阶段

- Multi\-Agent

- Browser Agent

- Computer Use

---

## 第三阶段

- RAG

- Long\-term Memory

- Sandbox

- Observability

---

# 十一、最终目标

真正理解：

```Plain Text
AI Agent ≠ 神秘 AI
```

而是：

```Plain Text
由 LLM 驱动的自动化循环系统
```

当你真正亲手写出：

```Python
while True:
    think()
    act()
    observe()
```

你就已经进入 Agent Engineering 世界了。

