from functools import lru_cache

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.ai.catalog import catalog_snapshot
from app.ai.llm.factory import LLMFactory
from app.ai.prompts import RAVI_SYSTEM
from app.ai.rate_limit import wait_for_llm_slot
from app.ai.tools import RAVI_TOOLS


def _system_message() -> SystemMessage:
    return SystemMessage(content=f"{RAVI_SYSTEM}\n\nCurrent ShopKart catalog:\n{catalog_snapshot()}")


def _agent_node(state: MessagesState) -> dict:
    wait_for_llm_slot()
    llm = LLMFactory.create().bind_tools(RAVI_TOOLS)
    messages = [_system_message(), *state["messages"]]
    return {"messages": [llm.invoke(messages)]}


@lru_cache(maxsize=1)
def build_ravi_graph():
    workflow = StateGraph(MessagesState)
    workflow.add_node("ravi", _agent_node)
    workflow.add_node("tools", ToolNode(RAVI_TOOLS))
    workflow.add_edge(START, "ravi")
    workflow.add_conditional_edges("ravi", tools_condition, {"tools": "tools", END: END})
    workflow.add_edge("tools", "ravi")
    return workflow.compile()
