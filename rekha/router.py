"""
Layer 3: Query Router
Dispatches the query to the optimal execution path: Bypass RAG, invoke a structured tool, or select a targeted vector partition.
"""

import time
from typing import Optional, Dict, Any, List
from .types import RouterResult


class QueryRouter:
    def __init__(self, router_engine=None, namespaces: Optional[Dict[str, str]] = None):
        """
        Initialize QueryRouter.
        router_engine: Shared Laya Router instance
        namespaces: Mapping of vector partition names to descriptions
        """
        self._router = router_engine
        self._namespaces = namespaces or {
            "general_knowledge": "General documentation, product guides, FAQs",
            "billing_policies": "Pricing, refunds, enterprise subscription agreements, invoices",
            "technical_specs": "API schemas, SDK usage, error codes, system uptime"
        }

    def _get_router(self):
        if self._router is None:
            from laya import Router
            self._router = Router()
        return self._router

    def evaluate(self, query: str) -> RouterResult:
        """
        Determine the execution destination for the user query.
        """
        start_time = time.perf_counter()

        router = self._get_router()
        state = {"query": query}

        # 1. Routing destination questions
        questions = {
            "execution_path": {
                "type": "choice",
                "instructions": (
                    "Decide which pipeline path is best for this user query. "
                    "Pick 'bypass' for simple greetings, acknowledgments, or conversational pleasantries. "
                    "Pick 'tool' if the query asks for real-time order/user lookup with specific IDs. "
                    "Pick 'vector_rag' if the user asks a knowledge question needing document lookup."
                ),
                "criteria": {
                    "bypass": "Greetings, 'hello', 'thank you', 'bye', chit-chat",
                    "tool": "Order lookup, specific account balance check, live ticket status with ID",
                    "vector_rag": "How-to questions, policies, explanations, documentation lookup"
                }
            },
            "namespace": {
                "type": "choice",
                "instructions": "If this query needs document lookup, which category best fits?",
                "criteria": self._namespaces
            },
            "reasoning_complexity": {
                "type": "score",
                "instructions": "Rate how complex or multi-step this question is from 1 (simple fact) to 5 (deep reasoning).",
                "min": 1,
                "max": 5
            }
        }

        try:
            res = router.predict(state=state, questions=questions)
            
            path_choice = res.get("choices", {}).get("execution_path", {}).get("choice", "vector_rag")
            path_prob = res.get("choices", {}).get("execution_path", {}).get("probability", 1.0)
            
            ns_choice = res.get("choices", {}).get("namespace", {}).get("choice", "general_knowledge")
            complexity = res.get("scores", {}).get("reasoning_complexity", {}).get("score", 1)

            dest_map = {
                "bypass": "BYPASS_NO_RAG",
                "tool": "STRUCTURED_TOOL",
                "vector_rag": "VECTOR_SEARCH"
            }
            destination = dest_map.get(path_choice, "VECTOR_SEARCH")

        except Exception:
            destination = "VECTOR_SEARCH"
            ns_choice = "general_knowledge"
            complexity = 1
            path_prob = 1.0

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return RouterResult(
            destination=destination,
            target_namespace=ns_choice,
            estimated_complexity=complexity,
            confidence=path_prob,
            latency_ms=elapsed_ms
        )
