"""工具定义与执行"""

import datetime
import subprocess
import rag

# ---- 工具定义（JSON Schema 格式，告诉 LLM 每个工具怎么用）----

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气（模拟数据）",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如 Beijing",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如 123 * 456",
                    },
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "执行一条 shell 命令并返回输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 shell 命令",
                    },
                },
                "required": ["command"],
            },
        },
    },
    rag.TOOL_DEFINITION,
]

# ---- 编码处理 ----

def _decode_bytes(raw: bytes) -> str:
    """尝试多种编码解码 shell 输出，优先 UTF-8，失败则用 GBK"""
    # Windows 上 shell 输出可能在 UTF-8 和 GBK 之间
    for encoding in ("utf-8", "gbk", "cp936", "latin-1"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


# ---- 工具执行 ----

_WEATHER_DATA = {
    "beijing": "晴，25°C，湿度 40%",
    "北京": "晴，25°C，湿度 40%",
    "shanghai": "多云，28°C，湿度 65%",
    "上海": "多云，28°C，湿度 65%",
    "shenzhen": "阵雨，30°C，湿度 80%",
    "深圳": "阵雨，30°C，湿度 80%",
    "tokyo": "晴，22°C，湿度 50%",
    "东京": "晴，22°C，湿度 50%",
}


def execute(name: str, arguments: dict) -> str:
    """根据工具名称和参数执行工具，返回结果字符串"""
    if name == "get_current_time":
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if name == "get_weather":
        city = arguments.get("city", "").lower()
        return _WEATHER_DATA.get(city, f"暂无 {city} 的天气数据")

    if name == "calculate":
        expression = arguments.get("expression", "")
        try:
            result = eval(expression, {"__builtins__": {}})
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"

    if name == "run_shell":
        command = arguments.get("command", "")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=10,
            )
            # 拿到原始 bytes，尝试多种编码解码
            raw = result.stdout or result.stderr or b""
            output = _decode_bytes(raw)
            return output.strip() or "(无输出，命令执行成功)"
        except subprocess.TimeoutExpired:
            return "命令执行超时"
        except Exception as e:
            return f"命令执行失败: {e}"

    if name == "search_document":
        query = arguments.get("query", "")
        return rag.execute(query)

    return f"未知工具: {name}"
