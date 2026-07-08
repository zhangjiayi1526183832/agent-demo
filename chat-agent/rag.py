"""RAG — 检索增强生成（最简版：关键词匹配，不需要向量数据库）"""

import os

# ---- 文档存储 ----
_chunks = []          # [(filename, chunk_index, text), ...]
_doc_names = set()


# ---- 工具定义 ----

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_document",
        "description": "搜索已加载的文档，返回与查询最相关的文本片段",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题",
                },
            },
            "required": ["query"],
        },
    },
}


# ---- 文档加载与切片 ----

def load_document(filepath: str, chunk_size: int = 400) -> int:
    """加载一个文本文件，切成块，返回块数量"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    filename = os.path.basename(filepath)
    if filename in _doc_names:
        return 0  # 已加载过

    _doc_names.add(filename)
    added = 0
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # 尝试在句号或换行处截断，避免从半句话中断
        if end < len(text):
            for sep in ("\n\n", "\n", "。", ". "):
                pos = text.rfind(sep, start, end)
                if pos > start + chunk_size // 2:
                    end = pos + 1
                    break
        chunk = text[start:end].strip()
        if chunk:
            _chunks.append((filename, idx, chunk))
            added += 1
            idx += 1
        start = end

    return added


# ---- 检索 ----

def _score(query: str, chunk: str) -> float:
    """简单的关键词匹配评分"""
    query_lower = query.lower()
    chunk_lower = chunk.lower()
    score = 0
    # 整个 query 出现的次数
    score += chunk_lower.count(query_lower) * 10
    # 每个词单独匹配
    for word in query_lower.split():
        score += chunk_lower.count(word) * 2
    return score


def search(query: str, top_k: int = 3) -> list[dict]:
    """搜索最相关的文档片段"""
    if not _chunks:
        return []

    scored = []
    for filename, idx, text in _chunks:
        s = _score(query, text)
        if s > 0:
            scored.append((s, filename, idx, text))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {"source": f"{filename}[片段{idx}]", "content": text}
        for _, filename, idx, text in scored[:top_k]
    ]


# ---- 工具执行入口 ----

def execute(query: str) -> str:
    """search_document 工具的执行函数"""
    if not _chunks:
        return "(未加载任何文档。请先用 /load <文件路径> 加载文档)"

    results = search(query)
    if not results:
        return f"(在已加载的 {len(_chunks)} 个片段中，未找到与 \"{query}\" 相关的内容)"

    lines = [f"找到 {len(results)} 条相关片段:\n"]
    for r in results:
        lines.append(f"--- {r['source']} ---")
        lines.append(r["content"])
        lines.append("")
    return "\n".join(lines)


def status() -> str:
    """返回当前已加载文档的状态"""
    if not _chunks:
        return "未加载任何文档"
    return f"已加载 {len(_doc_names)} 个文档，共 {len(_chunks)} 个片段"
