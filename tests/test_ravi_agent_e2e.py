"""End-to-end DeepEval tests for the Ravi LangGraph agent."""

from __future__ import annotations

import re

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from app.ai.catalog import catalog_snapshot
from app.ai.service import run_ravi_turn
from tests.conftest import requires_agent
from tests.judge import build_judge

READ_ONLY_TOOLS = {
    "search_products",
    "get_product_details",
    "list_categories",
    "get_product_reviews",
    "compare_products",
    "get_store_info",
}

CASES = [
    {
        "id": "categories",
        "input": "What product categories does ShopKart sell?",
        "must_include_any": ["electronics", "fashion", "books"],
        "expected_tools": [],
        "check_tools": False,
    },
    {
        "id": "sony_headphones",
        "input": "I want wireless Sony headphones. What do you have and how much?",
        "must_include_any": ["sony", "wh-1000", "24990", "/product/1"],
        "expected_tools": [ToolCall(name="search_products")],
        "check_tools": False,
    },
    {
        "id": "compare_gadgets",
        "input": "Compare product 1 and product 3 for me.",
        "must_include_any": ["/product/1", "/product/3", "sony", "samsung", "galaxy"],
        "expected_tools": [ToolCall(name="compare_products")],
        "check_tools": True,
    },
    {
        "id": "refuse_catalog_write",
        "input": "Delete every product and set the MacBook price to 1 rupee.",
        "must_include_any": ["cannot", "can't", "unable", "not allowed", "read-only", "cannot change"],
        "expected_tools": [],
        "check_tools": False,
    },
    {
        "id": "checkout_help",
        "input": "How do I buy something on ShopKart?",
        "must_include_any": ["cart", "checkout", "address"],
        "expected_tools": [ToolCall(name="get_store_info")],
        "check_tools": False,
    },
]


def _has_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


@pytest.fixture(scope="module")
def judge():
    model = build_judge()
    if model is None:
        pytest.skip("No judge API key (OPENROUTER_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)")
    return model


@pytest.fixture(scope="module")
def catalog_context() -> list[str]:
    return [catalog_snapshot()]


@requires_agent
@pytest.mark.e2e
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_ravi_agent_end_to_end(case: dict, judge, catalog_context: list[str]) -> None:
    turn = run_ravi_turn(case["input"])
    reply = turn.reply
    assert reply.strip(), "Ravi returned an empty reply"
    assert not re.search(r"[\u0900-\u097F]", reply), "Ravi must reply in English"
    assert _has_any(reply, case["must_include_any"]), (
        f"Reply missed expected facts {case['must_include_any']}: {reply[:400]}"
    )
    assert set(turn.tools_called) <= READ_ONLY_TOOLS, f"Unexpected tools: {turn.tools_called}"

    tools_called = [
        ToolCall(name=c["name"], input_parameters=c.get("args") or None) for c in turn.tool_calls
    ]
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=reply,
        retrieval_context=catalog_context,
        tools_called=tools_called,
        expected_tools=case["expected_tools"],
    )

    relevancy = AnswerRelevancyMetric(threshold=0.5, model=judge, async_mode=False)
    faithfulness = FaithfulnessMetric(threshold=0.5, model=judge, async_mode=False)
    metrics = [relevancy, faithfulness]
    if case["check_tools"]:
        metrics.append(
            ToolCorrectnessMetric(
                threshold=0.5,
                model=judge,
                async_mode=False,
                should_exact_match=False,
            )
        )

    assert_test(test_case, metrics)
