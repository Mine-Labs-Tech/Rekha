"""
Enterprise Test Suite: Layer 5 Outbound Grounding & Verification Gate
Tests negative constraint enforcement, concrete entity anchoring ($ amounts, SLAs, dates), and hallucination blocking.
"""

import pytest
from rekha.verifier import VerificationGate
from rekha.types import VerificationResult


@pytest.fixture(scope="module")
def verifier():
    return VerificationGate()


class TestVerificationGateEnterprise:
    def test_fully_grounded_answer_approved(self, verifier):
        """Answer strictly matching reference facts must pass with STREAM_TO_USER."""
        reference = (
            "Acme Cloud offers the Pro plan for $199/month including 25 seats and 1 TB storage. "
            "Refunds are guaranteed within the first 30 days."
        )
        answer = (
            "The Pro plan is priced at $199/month and includes 25 seats. Customers can request "
            "a refund within the initial 30 days."
        )
        result: VerificationResult = verifier.verify(
            query="What is the Pro plan price and refund window?",
            reference_context=reference,
            generated_answer=answer
        )
        assert result.is_supported is True
        assert result.decision == "STREAM_TO_USER"
        assert len(result.unanchored_entities) == 0

    def test_unanchored_numerical_hallucination_detected(self, verifier):
        """Answer fabricating prices or percentages not in reference must flag unanchored entities."""
        reference = (
            "Acme Cloud offers the Starter plan for $49/month with 5 seats."
        )
        # LLM hallucinates $19/month and 99.999%
        hallucinated_answer = (
            "The Starter plan is currently discounted to $19/month with a 99.999% uptime guarantee."
        )
        result: VerificationResult = verifier.verify(
            query="How much is the Starter plan?",
            reference_context=reference,
            generated_answer=hallucinated_answer
        )
        assert "$19" in result.unanchored_entities or "99.999%" in result.unanchored_entities

    def test_negative_constraint_competitor_mention_blocked(self, verifier):
        """Must block answers that violate negative constraint forbidding competitor recommendations."""
        reference = "Acme Cloud provides high-performance managed GPU instances."
        answer = "Acme Cloud is great, but you should also check out AWS EC2 or Microsoft Azure for better pricing."
        
        result: VerificationResult = verifier.verify(
            query="Where can I run my GPU workloads?",
            reference_context=reference,
            generated_answer=answer,
            negative_constraints=[
                "Do not recommend or mention competitors like AWS, Azure, or Google Cloud"
            ]
        )
        assert result.is_supported is False
        assert result.decision == "BLOCK_AND_FALLBACK"
        assert len(result.negative_constraints_violated) > 0

    def test_negative_constraint_illegal_refund_promise_blocked(self, verifier):
        """Must block answers that promise refunds beyond the legal 30-day window."""
        reference = "Refunds are eligible within 30 days only. After 30 days, charges are non-refundable."
        answer = "Our customer support team will gladly issue you a 100% full refund even after 90 days."
        
        result: VerificationResult = verifier.verify(
            query="Can I get a refund after 3 months?",
            reference_context=reference,
            generated_answer=answer,
            negative_constraints=[
                "Do not promise or allow refunds after 30 days"
            ]
        )
        assert result.is_supported is False
        assert result.decision == "BLOCK_AND_FALLBACK"
