# AI Agent 从 0 到 1 — 手写 Chat Agent 项目

## 项目说明

基于《从 0 到 1 手写 AI Chat Agent 学习路线》，从底层实现一个 AI Chat Agent，不依赖任何 Agent 框架。

## 当前进度

- [x] Day 1: 第一个 ChatBot — 调用 API 实现单轮问答
- [x] Day 2: Context — 维护消息列表实现多轮记忆
- [x] Day 3: System Prompt — AI 人格与行为规则
- [x] Day 4: Tool Calling
- [x] Day 5: Agent Loop
- [x] Day 6: 记忆与状态管理
- [x] Day 7: 完整 Chat Agent

## 项目结构

```
chat-agent/
├── main.py        # CLI 入口，聊天循环
├── llm.py         # LLM API 调用（HTTP 请求）
├── tools.py       # 工具定义（Day 4 开始）
├── memory.py      # 记忆管理（Day 2/6）
├── prompts.py     # System Prompt 模板（Day 3 开始）
├── .env           # API 配置（不提交）
├── .env.example   # API 配置模板
└── history.json   # 聊天记录存储

sessions/          # Claude 会话记录（用于跨终端恢复）
AI Agent 从0到1 学习笔记.md   # 学习笔记
```

## 技术栈

- Python — 纯 requests 调用，不依赖 OpenAI SDK
- DeepSeek API（兼容 OpenAI 格式）
- `pip install requests python-dotenv`

## 恢复 Claude 会话

在新终端拉取项目后：

1. 将 `sessions/` 下的 `.jsonl` 文件复制到对应位置：
   ```
   ~/.claude/projects/c--Users-ezra-zhang-Desktop-agent-demo/
   ```

2. 或者直接让 Claude Code 读取 `sessions/` 目录下的会话文件来了解当前进度。

## 学习理念

- 问题驱动：每步先暴露问题，再引入解决方案
- 极简代码：每天不超过 300 行，重在理解原理
- 学习笔记记录在 `AI Agent 从0到1 学习笔记.md`
