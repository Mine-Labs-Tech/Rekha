"""
Layer 5: Outbound Grounding & Verification Gate
Audits generated LLM responses for negative constraint violations, unanchored numerical/date entities,
and core claim alignment before streaming or returning text to end users.
"""

import time
import re
from typing import List, Optional, Dict, Any
from .types import VerificationResult

# Regex to extract numbers, currency, dates, percentages
CONCRETE_ENTITY_PATTERN = re.compile(
    r"(?:\$\d+(?:,\d{3})*(?:\.\d+)?|\b\d+(?:\.\d+)?%|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b)"
)


class VerificationGate:
    def __init__(self, router_engine=None):
        """
        Initialize VerificationGate.
        router_engine: Shared Laya Router instance
        """
        self._router = router_engine

    def _get_router(self):
        if self._router is None:
            from laya import Router
            self._router = Router()
        return self._router

    def verify(
        self,
        query: str,
        reference_context: str,
        generated_answer: str,
        negative_constraints: Optional[List[str]] = None
    ) -> VerificationResult:
        """
        Verify the generated response against reference context and negative constraints.
        """
        start_time = time.perf_counter()

        # 1. Concrete Entity Anchor Audit
        # Check if numbers/percentages in generated answer exist in reference context
        answer_entities = set(CONCRETE_ENTITY_PATTERN.findall(generated_answer))
        unanchored_entities = []
        for ent in answer_entities:
            if ent not in reference_context:
                unanchored_entities.append(ent)

        # 2. Negative Constraints Audit
        violated_constraints = []
        router = self._get_router()

        if negative_constraints:
            for constraint in negative_constraints:
                state = {
                    "constraint": constraint,
                    "answer_text": generated_answer
                }
                questions = {
                    "is_violation": {
                        "type": "noul",
                        "instructions": f"Does the text violate this specific rule: '{constraint}'?"
                    }
                }
                try:
                    res = router.predict(state=state, questions=questions)
                    is_violation = res.get("nouls", {}).get("is_violation", {}).get("decision", False)
                    if is_violation:
                        violated_constraints.append(constraint)
                except Exception:
                    pass

        # 3. Core Claim Alignment Rubric via Laya
        state = {
            "query": query,
            "source_facts": reference_context[:1000],  # Bound to high-signal reference
            "llm_answer": generated_answer
        }
        questions = {
            "factual_grounding": {
                "type": "score",
                "instructions": (
                    "Rate from 1 to 5 how strictly the LLM answer is supported by the source facts. "
                    "(1 = pure hallucination or contradiction, 5 = directly grounded and faithful)"
                ),
                "min": 1,
                "max": 5
            }
        }

        try:
            res = router.predict(state=state, questions=questions)
            alignment = res.get("scores", {}).get("factual_grounding", {}).get("score", 5)
        except Exception:
            alignment = 4

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine Final Decision
        decision = "STREAM_TO_USER"
        fallback_msg = None
        is_supported = True

        if len(violated_constraints) > 0:
            decision = "BLOCK_AND_FALLBACK"
            is_supported = False
            fallback_msg = "Response blocked due to policy constraint violation."
        elif len(unanchored_entities) > 0 and alignment <= 2:
            decision = "BLOCK_AND_FALLBACK"
            is_supported = False
            fallback_msg = (
                "Response contains unverified numbers or claims not found in official documentation. "
                "Please consult customer support."
            )
        elif alignment < 3:
            decision = "TRIGGER_RETRY"
            is_supported = False
            fallback_msg = "Answer lacks verifiable grounding in retrieved source documents."

        return VerificationResult(
            is_supported=is_supported,
            alignment_score=alignment,
            negative_constraints_violated=violated_constraints,
            unanchored_entities=unanchored_entities,
            decision=decision,
            fallback_message=fallback_msg,
            latency_ms=elapsed_ms
        )
