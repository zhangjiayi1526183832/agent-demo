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

# 十、进阶学习路线（重排）

当你真正理解：

- Context
- Prompt
- Tool Calling
- Loop
- State

之后再进入。

> **学习原则不变**：问题驱动（每步先知道为什么需要它）、不依赖框架（先从底层实现）、极简代码（理解原理而不是做产品）。

---

## 第一阶段：打磨基础（让现有 Agent 更好用）

### Streaming（流式输出）

**为什么需要**：当前 Agent 等 3 秒突然蹦一大段。流式输出让 AI 一个字一个字打出来——用户不用盯着空白屏幕等。

**是什么**：API 返回 `stream=True`，数据通过 SSE（Server-Sent Events）逐 chunk 到达，每个 chunk 包含几个字符。不是"生成完才返回"，而是"边生成边返回"。

**改动范围**：只改 `llm.py`，其他模块不受影响。

### Async（工具并行调用）

**为什么需要**：当前 `for tc in tool_calls` 是串行的——查北京天气要等上海天气查完才能开始。查 10 个城市的天气需要 10 次串行等待。

**是什么**：`asyncio` + `aiohttp`，多个 HTTP 请求同时发出，最快的结果先到达。查北京和上海天气同时发出，总耗时等于最慢的那一个，而不是两个相加。

**改动范围**：`llm.py`（异步 HTTP）、`main.py`（agent_loop 异步化）、`tools.py`（工具执行保持同步即可）。

### Observability（可观测性）

**为什么需要**：`/debug` 只能看表面。Agent 调用失败时，你无法回答"哪一步慢了？消耗了多少 token？LLM 当时在看什么 messages？"

**是什么**：结构化日志记录每一步的细节——耗时、token 消耗、工具调用链、messages 快照。给 Agent 加一个"黑匣子"。

**改动范围**：新增 `logger.py`，在 `agent_loop` 和 `chat` 里打点。

---

## 第二阶段：给 Agent 更多能力

### RAG（检索增强生成）

**为什么需要**：当前 Agent 只有 prompt 里的知识和假天气数据。你给它一个 PDF 它读不了，问它今天的最新动态它不知道。

**是什么**：Retrieval-Augmented Generation。把外部文档切成小块 → 存到向量数据库 → 用户提问时检索最相关的内容 → 塞进 prompt 让 LLM 参考回答。

**改动范围**：新增文档加载、文本切分、向量检索模块。

### Long-term Memory（长期记忆 — 向量数据库）

**为什么需要**：`history.json` 是一维的——只能按时间顺序取。你无法问"上次我们聊过的那个 Bug 是什么原因？"——因为 JSON 不会搜索语义。

**是什么**：把对话内容向量化存到数据库，查询时按语义相似度检索，而不是按时间。

**改动范围**：升级 `memory.py`，引入向量存储（如 ChromaDB、SQLite-vec）。

### MCP（标准化工具协议）

**为什么需要**：每个工具都要写 JSON Schema + execute 函数。如果团队有 10 个 Agent、50 个工具，每次加工具都要改代码。而且别人写的工具你没法复用。

**是什么**：Model Context Protocol。一套标准化的工具描述和调用协议，让工具定义和 Agent 解耦。类似 USB 协议——只要符合标准，任何工具都能插入任何 Agent。

**改动范围**：`tools.py` 改为从 MCP Server 加载工具。

---

## 第三阶段：复杂 Agent 系统

### Sandbox（安全执行环境）

**为什么需要**：你的 `run_shell` 能执行任意命令——`rm -rf /`、`curl 恶意链接`。当前没有任何安全隔离。

**是什么**：把工具执行放到 Docker 容器或虚拟机里。Agent 的操作不会影响宿主机。

### Multi-Agent（多 Agent 协作）

**为什么需要**：一个 Agent 处理复杂任务时会迷失——既要写代码、又要查文档、又要写测试，上下文越堆越多导致决策质量下降。

**是什么**：任务分拆给多个 Agent 并行/串行处理——"你负责写代码，你负责写测试，你负责审查"。每个 Agent 只关注自己的领域。

### Browser Agent / Computer Use

**为什么需要**：当前 Agent 只能调工具和聊天。如果任务需要"打开网页、登录、填写表单、截图"，你的工具有限。

**是什么**：给 Agent 浏览器操作能力（Playwright）或桌面操控能力。Agent 能"看"屏幕、"操作"界面。

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

