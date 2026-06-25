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

### Async（工具并行调用）

---

### Observability（可观测性）

---

## 第二阶段：给 Agent 更多能力

### RAG（检索增强生成）

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
