"""
Enterprise Test Suite: Layer 2 Inbound Cache Gate
Tests canonical intent matching, semantic rephrasing, false-positive resistance, and boundary isolation.
"""

import pytest
import time
from rekha.cache import CacheGate
from rekha.types import CacheResult


@pytest.fixture(scope="module")
def populated_cache():
    gate = CacheGate(maxsize=100, ttl_seconds=3600)
    # Register 3 distinct canonical FAQs
    gate.register_canonical_intent(
        intent_id="faq_refund_period",
        description="Questions asking how many days or what time window is allowed for requesting a refund",
        answer="Acme Cloud offers a 100% money-back guarantee within the first 30 days of subscription."
    )
    gate.register_canonical_intent(
        intent_id="faq_uptime_sla",
        description="Questions asking about uptime service level agreements or downtime guarantees",
        answer="Enterprise subscriptions come with a contractually guaranteed 99.99% uptime SLA."
    )
    gate.register_canonical_intent(
        intent_id="faq_payment_methods",
        description="Questions asking which payment methods are accepted (credit cards, bank transfers, crypto)",
        answer="We accept Visa, Mastercard, AMEX, and ACH bank transfers. Cryptocurrency is strictly not accepted."
    )
    return gate


class TestCacheGateEnterprise:
    def test_exact_canonical_match(self, populated_cache):
        """Exact semantic question should hit canonical cache."""
        query = "What is the refund window and how many days do I have to request a refund?"
        result: CacheResult = populated_cache.evaluate(query)
        assert result.is_canonical is True
        assert result.cache_hit is True
        assert result.intent_id == "faq_refund_period"
        assert "30 days" in result.cached_payload

    def test_semantic_paraphrasing_hit(self, populated_cache):
        """Different wording asking the same intent should hit cache."""
        query = "Can I get my money back if I cancel within three weeks?"
        result: CacheResult = populated_cache.evaluate(query)
        assert result.is_canonical is True
        assert result.cache_hit is True
        assert result.intent_id == "faq_refund_period"

    def test_distinct_intent_isolation(self, populated_cache):
        """Query about payment methods must route to payment methods, NOT refund."""
        query = "Do you guys accept Bitcoin, Ethereum or credit cards for payment?"
        result: CacheResult = populated_cache.evaluate(query)
        assert result.is_canonical is True
        assert result.intent_id == "faq_payment_methods"
        assert "Cryptocurrency is strictly not accepted" in result.cached_payload

    def test_novel_non_canonical_query_miss(self, populated_cache):
        """
        CRITICAL FALSE-POSITIVE TEST:
        A novel/complex query must NOT falsely trigger a canonical cache hit.
        """
        query = "How do I configure OAuth 2.0 PKCE authentication with your Python SDK in a FastAPI app?"
        result: CacheResult = populated_cache.evaluate(query)
        assert result.is_canonical is False
        assert result.cache_hit is False
        assert result.cached_payload is None

    def test_cache_latency_overhead(self, populated_cache):
        """Cache evaluation overhead should be fast."""
        query = "What is the uptime SLA guarantee?"
        result: CacheResult = populated_cache.evaluate(query)
        assert result.latency_ms < 80.0
