from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage

from app.ai.graph import build_ravi_graph


def _as_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    return str(content or "").strip()


@dataclass
class RaviTurn:
    reply: str
    tools_called: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)


def _history_messages(message: str, history: list[dict] | None) -> list:
    messages: list = []
    for turn in (history or [])[-8:]:
        role = (turn.get("role") or "").lower()
        text = (turn.get("content") or "").strip()
        if not text:
            continue
        if role == "user":
            messages.append(HumanMessage(content=text))
        elif role in {"assistant", "ravi", "ai"}:
            messages.append(AIMessage(content=text))
    messages.append(HumanMessage(content=message.strip()))
    return messages


def _extract_tool_calls(messages: list) -> list[dict]:
    calls: list[dict] = []
    for msg in messages:
        for tc in getattr(msg, "tool_calls", None) or []:
            if isinstance(tc, dict):
                name = tc.get("name") or ""
                args = tc.get("args") or {}
            else:
                name = getattr(tc, "name", "") or ""
                args = getattr(tc, "args", {}) or {}
            if name:
                calls.append({"name": name, "args": args})
    return calls


def run_ravi_turn(message: str, history: list[dict] | None = None) -> RaviTurn:
    graph = build_ravi_graph()
    result = graph.invoke({"messages": _history_messages(message, history)}, {"recursion_limit": 6})
    last = result["messages"][-1]
    text = _as_text(getattr(last, "content", last))
    reply = text or "I could not find a clear answer. Try asking about a product or category."
    tool_calls = _extract_tool_calls(result["messages"])
    return RaviTurn(
        reply=reply,
        tools_called=[c["name"] for c in tool_calls],
        tool_calls=tool_calls,
    )


def ask_ravi(message: str, history: list[dict] | None = None) -> str:
    return run_ravi_turn(message, history).reply
