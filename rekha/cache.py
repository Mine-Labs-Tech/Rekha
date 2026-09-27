"""
Layer 2: Inbound Cache Gate
Maps queries to discrete Canonical Intent Clusters, bypassing retrieval and LLM calls for known recurring answers.
"""

import time
from typing import Optional, Dict, Any
from cachetools import TTLCache
from .types import CacheResult


class CacheGate:
    def __init__(self, router_engine=None, maxsize: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize CacheGate.
        router_engine: Shared Laya Router instance
        maxsize: Max cached canonical answers in memory
        ttl_seconds: Cache TTL in seconds (default 1 hour)
        """
        self._router = router_engine
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        
        # Default canonical FAQ catalog: intent_id -> {"description": ..., "answer": ...}
        self._canonical_catalog: Dict[str, Dict[str, str]] = {}

    def _get_router(self):
        if self._router is None:
            from laya import Router
            self._router = Router()
        return self._router

    def register_canonical_intent(self, intent_id: str, description: str, answer: str):
        """
        Register a canonical intent with its verified answer.
        """
        self._canonical_catalog[intent_id] = {
            "description": description,
            "answer": answer
        }
        self._cache[intent_id] = answer

    def evaluate(self, query: str) -> CacheResult:
        """
        Check if query matches a known canonical intent with high confidence.
        """
        start_time = time.perf_counter()

        if not self._canonical_catalog:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return CacheResult(is_canonical=False, latency_ms=elapsed_ms)

        # Build criteria map from registered canonical catalog
        criteria = {
            k: v["description"] for k, v in self._canonical_catalog.items()
        }
        criteria["other_unmatched"] = "Any query that does not clearly ask about one of the specific topics above."

        router = self._get_router()
        state = {"user_query": query}
        questions = {
            "canonical_intent": {
                "type": "choice",
                "instructions": "Determine if the user is asking a standard canonical question from the options below.",
                "criteria": criteria
            }
        }

        try:
            res = router.predict(state=state, questions=questions)
            choice_data = res.get("choices", {}).get("canonical_intent", {})
            matched_intent = choice_data.get("choice")
            confidence = choice_data.get("probability", 0.0)

            # High-confidence threshold
            if matched_intent and matched_intent != "other_unmatched" and confidence >= 0.88:
                cached_answer = self._cache.get(matched_intent)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return CacheResult(
                    is_canonical=True,
                    intent_id=matched_intent,
                    intent_confidence=confidence,
                    cache_hit=(cached_answer is not None),
                    cached_payload=cached_answer,
                    latency_ms=elapsed_ms
                )

        except Exception:
            pass

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return CacheResult(
            is_canonical=False,
            latency_ms=elapsed_ms
        )
