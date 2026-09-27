"""
RekhaGateway: The Unified System-1 Control Plane Orchestrator.
Exposes the single-line `@gateway.protect` decorator and functional execution pipeline.
"""

import time
import functools
from typing import Callable, Optional, List, Dict, Any, Union
from .types import (
    RekhaPipelineResult,
    GuardResult,
    CacheResult,
    RouterResult,
    OptimizationStats,
    VerificationResult
)
from .guard import GuardGate
from .cache import CacheGate
from .router import QueryRouter
from .optimizer import ContextOptimizer
from .verifier import VerificationGate


class RekhaGateway:
    def __init__(
        self,
        enable_guard: bool = True,
        enable_cache: bool = True,
        enable_router: bool = True,
        enable_optimizer: bool = True,
        enable_verifier: bool = True,
        negative_constraints: Optional[List[str]] = None,
        target_context_reduction: float = 0.50
    ):
        """
        Initialize the Rekha Gateway.
        All modules share a single local Laya Router instance for efficiency.
        """
        from laya import Router
        self._shared_router = Router()

        self.enable_guard = enable_guard
        self.enable_cache = enable_cache
        self.enable_router = enable_router
        self.enable_optimizer = enable_optimizer
        self.enable_verifier = enable_verifier

        self.negative_constraints = negative_constraints or []
        self.target_context_reduction = target_context_reduction

        # Instantiate the 5 Gate Layers
        self.guard = GuardGate(router_engine=self._shared_router)
        self.cache = CacheGate(router_engine=self._shared_router)
        self.router = QueryRouter(router_engine=self._shared_router)
        self.optimizer = ContextOptimizer(router_engine=self._shared_router)
        self.verifier = VerificationGate(router_engine=self._shared_router)

    def register_canonical_faq(self, intent_id: str, description: str, verified_answer: str):
        """
        Register a canonical intent for instant sub-5ms cache bypass.
        """
        self.cache.register_canonical_intent(intent_id, description, verified_answer)

    def execute(
        self,
        query: str,
        rag_executor: Callable[[str, Optional[str]], tuple[str, Union[str, List[str]]]]
    ) -> RekhaPipelineResult:
        """
        Execute the full inbound-to-outbound control plane around a RAG executor.
        rag_executor: A function taking (query, optimized_context) and returning (candidate_answer, context_used).
        """
        start_total = time.perf_counter()

        # -----------------------------------------------------------------
        # LAYER 1: INBOUND GUARD GATE (< 15ms)
        # -----------------------------------------------------------------
        guard_res = GuardResult()
        if self.enable_guard:
            guard_res = self.guard.evaluate(query)
            if not guard_res.is_safe:
                elapsed_total = (time.perf_counter() - start_total) * 1000
                refusal_message = (
                    "Security Alert: Request blocked due to potential prompt injection or unsafe content."
                )
                return RekhaPipelineResult(
                    query=query,
                    final_output=refusal_message,
                    source="BLOCKED_GUARD",
                    guard=guard_res,
                    cache=CacheResult(),
                    router=RouterResult(),
                    total_overhead_latency_ms=elapsed_total
                )

        # -----------------------------------------------------------------
        # LAYER 2: INBOUND CACHE GATE (< 10ms)
        # -----------------------------------------------------------------
        cache_res = CacheResult()
        if self.enable_cache:
            cache_res = self.cache.evaluate(query)
            if cache_res.cache_hit and cache_res.cached_payload:
                elapsed_total = (time.perf_counter() - start_total) * 1000
                return RekhaPipelineResult(
                    query=query,
                    final_output=cache_res.cached_payload,
                    source="CACHE",
                    guard=guard_res,
                    cache=cache_res,
                    router=RouterResult(),
                    total_overhead_latency_ms=elapsed_total
                )

        # -----------------------------------------------------------------
        # LAYER 3: QUERY ROUTER (< 15ms)
        # -----------------------------------------------------------------
        router_res = RouterResult()
        if self.enable_router:
            router_res = self.router.evaluate(query)
            if router_res.destination == "BYPASS_NO_RAG":
                elapsed_total = (time.perf_counter() - start_total) * 1000
                return RekhaPipelineResult(
                    query=query,
                    final_output="Hello! How can I assist you with our product or documentation today?",
                    source="DIRECT_ROUTER",
                    guard=guard_res,
                    cache=cache_res,
                    router=router_res,
                    total_overhead_latency_ms=elapsed_total
                )

        # -----------------------------------------------------------------
        # EXECUTE EXISTING RAG & LAYER 4: CONTEXT OPTIMIZER
        # -----------------------------------------------------------------
        # Call user's RAG pipeline
        candidate_answer, raw_context = rag_executor(query, router_res.target_namespace)

        opt_stats: Optional[OptimizationStats] = None
        reference_text = raw_context if isinstance(raw_context, str) else "\n\n".join(raw_context)

        if self.enable_optimizer and reference_text:
            opt_res = self.optimizer.optimize(
                query=query,
                documents=reference_text,
                target_reduction=self.target_context_reduction
            )
            opt_stats = opt_res.stats
            reference_text = opt_res.optimized_context

        # -----------------------------------------------------------------
        # LAYER 5: OUTBOUND GROUNDING & VERIFICATION (< 35ms)
        # -----------------------------------------------------------------
        ver_res = VerificationResult()
        final_answer = candidate_answer
        source_tag = "RAG_VERIFIED"

        if self.enable_verifier and reference_text:
            ver_res = self.verifier.verify(
                query=query,
                reference_context=reference_text,
                generated_answer=candidate_answer,
                negative_constraints=self.negative_constraints
            )
            if ver_res.decision == "BLOCK_AND_FALLBACK":
                final_answer = ver_res.fallback_message or (
                    "Notice: The response could not be verified against official documentation."
                )
                source_tag = "RAG_FALLBACK"

        elapsed_total = (time.perf_counter() - start_total) * 1000

        return RekhaPipelineResult(
            query=query,
            final_output=final_answer,
            source=source_tag,
            guard=guard_res,
            cache=cache_res,
            router=router_res,
            optimizer=opt_stats,
            verifier=ver_res,
            total_overhead_latency_ms=elapsed_total
        )

    def protect(self, func: Callable):
        """
        Decorator that wraps an existing RAG function:
        @gateway.protect
        def my_rag(query: str, namespace: Optional[str] = None):
            ...
            return answer, context
        """
        @functools.wraps(func)
        def wrapper(query: str, *args, **kwargs):
            return self.execute(query, rag_executor=lambda q, ns: func(q, *args, **kwargs))
        return wrapper
