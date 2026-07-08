# AI Agent 进阶学习笔记

> 完成 7 天基础 Agent 后的进阶路线，继续以问题驱动的方式学习。
>
> 每节记录：
> 1. 为什么需要 — 现有 Agent 的什么痛点触发
> 2. 是什么 — 概念解释
> 3. 怎么实现 — 核心代码改动
> 4. 核心理解 — 一句话总结

---

## 第一阶段：打磨基础

### Streaming（流式输出）（2026-06-24）

#### 为什么需要

Day 1-7 的 `chat()` 是"一次性模式"：

```
发送请求 → [等待 4 秒，屏幕空白] → 整段文字突然出现
```

用户体验很差——不知道 AI 是否在工作。

#### 是什么

两种模式的对比：

```
常规模式（Day 1-7）：
  HTTP POST → API 生成完整回复 → 一次性返回 JSON

流式模式：
  HTTP POST (stream=True) → API 边生成边返回 token
  → HTTP 连接保持打开，数据通过 SSE 逐 chunk 到达
```

HTTP 层面的区别：

```
常规响应:
  Content-Type: application/json
  Body: {"choices": [{"message": {"content": "全部文字"}}]}

流式响应 (SSE):
  Content-Type: text/event-stream
  data: {"choices": [{"delta": {"content": "面"}}]}
  data: {"choices": [{"delta": {"content": "向"}}]}
  data: {"choices": [{"delta": {"content": "对"}}]}
  ...
  data: [DONE]
```

#### 怎么实现

**llm.py** — 新增 `chat_stream()` 生成器：

```python
def chat_stream(messages, tools=None):
    # 1. stream=True
    response = requests.post(..., stream=True)

    # 2. 逐行读取 SSE，累积拼接
    accumulated_content = ""
    accumulated_tool_calls = {}

    for line in response.iter_lines():
        if line.startswith("data: "):
            chunk = json.loads(line[6:])
            delta = chunk["choices"][0]["delta"]

            if "content" in delta:
                yield ("text", delta["content"])      # 逐字输出

            # tool_calls 分片累积
            for tc in delta.get("tool_calls", []):
                idx = tc["index"]
                accumulated_tool_calls[idx]["function"]["name"] += tc["function"]["name"]

    # 3. 返回完整消息
    yield ("done", {"content": ..., "tool_calls": [...]})
```

**main.py** — `agent_loop()` 改为流式：

```python
for event_type, data in chat_stream(messages, tools):
    if event_type == "text":
        sys.stdout.write(data)     # 逐字打印
        sys.stdout.flush()
    elif event_type == "done":
        if data["tool_calls"]:
            execute(...)            # 工具调用
            break
        else:
            return data["content"]  # 最终回复
```

#### 关键细节：tool_calls 在流式中的分片累积

流式模式下 tool_calls 可能分多个 chunk 到达，需要累积拼接：

```
chunk 1: delta.tool_calls[0] = {"function": {"name": "get_", ...}}
chunk 2: delta.tool_calls[0] = {"function": {"name": "current_time", ...}}
chunk 3: delta.tool_calls[0] = {"function": {"arguments": "{}"}}
```

#### 核心理解

Streaming 只是**传输方式**的改变。`agent_loop()` 结构完全不变——只是 `chat()` 换成了 `chat_stream()`。

---

### Async（工具并行调用）（2026-07-06）

#### 为什么需要

当前工具执行是串行的：

```python
for tc in tool_calls:
    execute(name, args)   # 等 → 等 → 等
```

4 个城市天气 = 4 次串行 = 耗时相加。但它们互不依赖，完全可以同时查。

#### 是什么

```
同步 (requests)              异步 (aiohttp + asyncio)
  send → wait → recv            send1 + send2 + send3 + send4
  send → wait → recv            ↓ 全部发出
  send → wait → recv            recv(any order) → 全部收集
  send → wait → recv
  总时间 = T1+T2+T3+T4          总时间 = max(T1,T2,T3,T4)
```

核心机制：`await` 在等待一个 I/O 操作时不阻塞当前线程，事件循环可以切换到另一个任务。

#### 怎么实现

**llm.py** — 新增 `achat_stream()`，用 aiohttp 替代 requests：

```python
# 同步版：requests
response = requests.post(url, stream=True)
for line in response.iter_lines():
    ...

# 异步版：aiohttp  
async with aiohttp.ClientSession() as session:
    async with session.post(url, json=body) as resp:
        async for line in resp.content:     # ← async for 替代 for
            ...
```

结构一模一样，只换了 HTTP 库和加了 `async/await` 关键字。

**main.py** — `agent_loop` 改为异步 + 工具并行：

```python
async def agent_loop(messages, max_steps=10):
    ...
    async for event_type, data in achat_stream(messages, tools):  # async for
        ...

        # 工具并行执行：asyncio.gather + to_thread
        tasks = [
            asyncio.to_thread(execute, tc["function"]["name"], args)
            for tc in tool_calls
        ]
        results = await asyncio.gather(*tasks)
        # 4 个工具同时执行，总耗时 = 最慢的那个

async def main():
    ...
    await agent_loop(messages)

if __name__ == "__main__":
    asyncio.run(main())   # 启动事件循环
```

#### 关键细节

`asyncio.to_thread(func, *args)` — 把同步函数放到线程池执行，不阻塞事件循环。适合 I/O 密集型工具（网络请求、文件操作）。

`asyncio.gather(*tasks)` — 等待所有任务完成，返回结果列表。

#### 实测效果

4 个城市天气查询：

```
[TOOL] 调用: 北京   ← 4 个请求同时发出
[TOOL] 调用: 上海
[TOOL] 调用: 深圳
[TOOL] 调用: 东京
[TOOL] 结果: 上海   ← 返回顺序 ≠ 调用顺序（证明并行）
[TOOL] 结果: 北京
[TOOL] 结果: 东京
[TOOL] 结果: 深圳
```

#### 核心理解

`async/await` 不加速单个操作——它加速的是"多个 I/O 操作同时跑"的场景。

```python
# 同步：一个接一个
for task in tasks:
    await_io(task)     # 总耗时 = sum

# 异步：全部同时
await gather([await_io(t) for t in tasks])  # 总耗时 = max
```

---

### Observability（可观测性）（2026-07-07）

#### 为什么需要

`/debug` 的输出是一堆杂乱的 print，没有时间戳、没有统计、无法回溯。

```
[LOOP] === 第 1 轮 ===
[TOOL] 调用: get_weather
[TOOL] 结果: 晴，25°C              ← 什么时候发生的？花了多久？
```

你不知道哪一步耗时最长、整个对话花了多少轮、工具调了多少次。

#### 是什么

给 Agent 装上"黑匣子"——用结构化事件替代零散的 print：

```
[+0.000s] [AGENT_START] 开始处理，当前 4 条上下文消息
[+0.000s] [LLM] 第1轮API调用 → 消息4条 预估69tokens
[+1.354s] [TOOL] 调用: get_weather
[+1.355s] [TOOL_RESULT] get_weather → 晴，25°C，湿度 40%
[+1.356s] [LLM] 第2轮API调用 → 消息8条 预估165tokens
[+4.519s] [AGENT_END] 完成，共2轮 2次工具调用
────────────────────────────────────────
运行摘要:
  耗时: 4.52s
  事件数: 8
  LLM调用轮数: 2
  工具调用次数: 2
────────────────────────────────────────
```

每个事件都有：**相对时间戳 + 类型 + 详情**。运行结束后自动打印摘要 + 保存 `trace.json`。

#### 怎么实现

**logger.py** — Trace 类：

```python
class Trace:
    def __init__(self):
        self.events = []
        self.start_time = time.time()
        self.tool_count = 0

    def event(self, category, detail, **kwargs):
        ts = time.time() - self.start_time    # 相对时间
        self.events.append({"ts": ts, "category": category, "detail": detail})
        print(f"[+{ts:>6.3f}s] [{category.upper()}] {detail}")

    def summary(self):
        # 打印汇总统计

    def save(self, filepath="trace.json"):
        # 持久化到文件
```

**main.py** — 在 agent_loop 的关键节点打点：

```python
async def agent_loop(messages, max_steps=10):
    trace = Trace()
    trace.event("agent_start", f"开始...")

    while step < max_steps:
        trace.event("llm", f"第{step}轮...")
        ...
        trace.event("tool", f"调用: {name}")
        trace.event("tool_result", f"{name} → {result}")
        ...

    trace.event("agent_end", "完成")
    trace.summary()
    trace.save()
```

#### 核心理解

Observability = **给 Agent 的每一步打上时间戳和标签**。不是为了打印好看，而是让你在 Agent 出错时有东西可以回溯。

```python
# 之前：出错了，不知道发生了什么
# 之后：打开 trace.json，按时间线回放整个过程
```

---

## 第二阶段：给 Agent 更多能力

### RAG（检索增强生成）（2026-07-08）

#### 为什么需要

当前 Agent 的知识来源：训练数据 + System Prompt。无法回答关于**你的本地文件**的问题。

```
You: 这个项目的学习理念是什么？
AI: 不知道，我是通用AI。  ← 它没读过项目的文档
```

#### 是什么

RAG = 每次提问时，先从文档库**检索**相关内容，**注入** prompt，再让 LLM **生成**回答。

```
用户:"项目用什么技术栈？"
         │
         ▼
   1. 检索: search("技术栈") → 找到 CLAUDE.md 片段
         │
         ▼
   2. 注入: messages += "参考以下文档: [片段内容]"
         │
         ▼
   3. 生成: LLM 看到片段，回答 "Python + requests + DeepSeek API"
```

不是让 LLM 记住文档，而是**只在需要时检索，把相关内容塞进 prompt**。

#### 怎么实现

**rag.py** — 三个核心函数：

```python
# 1. 加载文档，切成块
def load_document(filepath, chunk_size=400):
    text = read_file(filepath)
    while start < len(text):
        chunk = text[start:start+chunk_size]  # 按尺寸切
        _chunks.append((filename, idx, chunk))

# 2. 关键词检索（不需向量数据库）
def search(query, top_k=3):
    for chunk in _chunks:
        score = chunk.count(query) * 10  # 简单评分
    return top_k_results

# 3. 格式化结果 → 注入 prompt
def execute(query):
    results = search(query)
    return format(results)  # → LLM 看到的 tool result
```

**tools.py** — 注册为工具：

```python
TOOL_DEFINITIONS = [..., rag.TOOL_DEFINITION]  # search_document

def execute(name, args):
    if name == "search_document":
        return rag.execute(args["query"])
```

**main.py** — `/load` 命令加载文档：

```python
/load ../CLAUDE.md  → 切成 4 个片段
/load ./README.md   → 再加载更多文档
```

#### 实测效果

```
You: 这个项目的学习理念是什么？
[TOOL] search_document("学习理念") → 找到 2 个相关片段
[TOOL] search_document("学习理念") → 补充搜索，找到 3 个
AI: 项目核心学习思想:
    - 从底层做起，不依赖框架
    - 循序渐进（Day 1→7）
    - 先理解原理，再动手实现
```

#### 当前局限

- **关键词匹配**：只能用词频评分，不理解语义（"学会"和"掌握"不会匹配）
- **无向量检索**：大文档库时性能差且精度低
- **片段硬切**：可能在句子中间截断

这些局限正好引出下一个主题：**向量数据库 + 语义检索**。

#### 核心理解

```python
# RAG 不是魔法，就三步
1. chunks = load_and_split(document)      # 切文档
2. relevant = search(query, chunks)        # 找相关
3. prompt = f"参考:{relevant}\n问题:{query}"  # 注入 → LLM 回答
```

---

### Long-term Memory（向量数据库）

---

### MCP（标准化工具协议）

---

## 第三阶段：复杂 Agent 系统

### Sandbox（安全执行环境）

---

### Multi-Agent（多 Agent 协作）

---

### Browser Agent / Computer Use

---
