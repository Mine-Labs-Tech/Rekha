"""
Enterprise Test Suite: Layer 3 Query Router
Tests tri-destination dispatching: BYPASS_NO_RAG, STRUCTURED_TOOL, and targeted VECTOR_SEARCH partitions.
"""

import pytest
from rekha.router import QueryRouter
from rekha.types import RouterResult


@pytest.fixture(scope="module")
def router():
    return QueryRouter()


class TestQueryRouterEnterprise:
    def test_conversational_greeting_bypass(self, router):
        """Conversational pleasantries must bypass expensive RAG."""
        queries = [
            "Hello there, good morning!",
            "Thank you so much for the assistance, that was all.",
            "Hi, is anyone available right now?"
        ]
        for q in queries:
            result: RouterResult = router.evaluate(q)
            assert result.destination == "BYPASS_NO_RAG", f"Failed on query: {q}"

    def test_operational_structured_tool_routing(self, router):
        """Operational queries with specific IDs should route to structured tools."""
        query = "Can you check the current shipping status of order tracking ID #884192?"
        result: RouterResult = router.evaluate(query)
        assert result.destination == "STRUCTURED_TOOL"

    def test_technical_vector_namespace_selection(self, router):
        """Technical API queries must route to VECTOR_SEARCH with technical namespace."""
        query = "What is the HTTP error code and retry-after header when rate limits are exceeded?"
        result: RouterResult = router.evaluate(query)
        assert result.destination == "VECTOR_SEARCH"
        assert result.target_namespace == "technical_specs"

    def test_billing_vector_namespace_selection(self, router):
        """Pricing and refund policy questions must route to billing partition."""
        query = "What are the exact pricing terms and refund eligibility rules for enterprise teams?"
        result: RouterResult = router.evaluate(query)
        assert result.destination == "VECTOR_SEARCH"
        assert result.target_namespace == "billing_policies"
