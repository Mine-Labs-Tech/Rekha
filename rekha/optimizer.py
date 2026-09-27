"""
Layer 4: Context Optimizer
Performs syntax-aware micro-slicing, parallel encoder relevance scoring, and knapsack budget packing.
Preserves markdown tables, code fencing, and natural document reading order.
"""

import time
import re
from typing import List, Optional, Union
from .types import SliceCandidate, OptimizationStats, OptimizationResult


# Regex for paragraph & sentence boundaries while preserving blocks
PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


class ContextOptimizer:
    def __init__(self, router_engine=None):
        """
        Initialize ContextOptimizer.
        router_engine: Shared Laya Router instance
        """
        self._router = router_engine

    def _get_router(self):
        if self._router is None:
            from laya import Router
            self._router = Router()
        return self._router

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Fast token estimation (~4 characters per token).
        """
        return max(1, len(text) // 4)

    def micro_slice(self, raw_text: str) -> List[str]:
        """
        Syntax-aware micro-slicer.
        Preserves Markdown code blocks, tables, and JSON objects.
        """
        slices: List[str] = []
        raw_blocks = PARAGRAPH_SPLIT.split(raw_text.strip())

        in_code_block = False
        code_buffer = []

        for block in raw_blocks:
            cleaned = block.strip()
            if not cleaned:
                continue

            # Handle code blocks intact
            if cleaned.startswith("```") or in_code_block:
                code_buffer.append(cleaned)
                if cleaned.endswith("```") and len(code_buffer) > 1:
                    slices.append("\n\n".join(code_buffer))
                    code_buffer = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            # Handle Markdown table rows intact
            if cleaned.startswith("|") and cleaned.endswith("|"):
                slices.append(cleaned)
                continue

            # If paragraph is long (> 60 words), split into sentence chunks
            sentences = SENTENCE_SPLIT.split(cleaned)
            if len(sentences) > 2 and len(cleaned) > 250:
                current_chunk = []
                current_len = 0
                for s in sentences:
                    current_chunk.append(s)
                    current_len += len(s)
                    if current_len >= 180:
                        slices.append(" ".join(current_chunk))
                        current_chunk = []
                        current_len = 0
                if current_chunk:
                    slices.append(" ".join(current_chunk))
            else:
                slices.append(cleaned)

        if code_buffer:
            slices.append("\n\n".join(code_buffer))

        return slices

    def optimize(
        self,
        query: str,
        documents: Union[str, List[str]],
        target_reduction: float = 0.50,
        min_relevance_threshold: int = 3
    ) -> OptimizationResult:
        """
        Optimize context for a user query.
        target_reduction: Fraction of noise to prune (default 50%)
        min_relevance_threshold: Minimum score (1-5) to retain a slice
        """
        start_time = time.perf_counter()

        # Consolidate raw documents
        if isinstance(documents, list):
            raw_text = "\n\n".join(documents)
        else:
            raw_text = documents

        original_tokens = self.estimate_tokens(raw_text)
        slices = self.micro_slice(raw_text)

        if not slices or len(slices) <= 1:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            stats = OptimizationStats(
                original_tokens=original_tokens,
                optimized_tokens=original_tokens,
                tokens_saved=0,
                compression_ratio=1.0,
                slices_total=len(slices),
                slices_retained=len(slices),
                latency_ms=elapsed_ms
            )
            return OptimizationResult(optimized_context=raw_text, stats=stats)

        # 2. Parallel Relevance Scoring via Laya
        router = self._get_router()
        candidates: List[SliceCandidate] = []

        # Evaluate candidate slices
        for idx, s in enumerate(slices):
            t_count = self.estimate_tokens(s)
            state = {
                "query": query,
                "candidate_passage": s
            }
            questions = {
                "relevance": {
                    "type": "score",
                    "instructions": (
                        "On a 1-5 scale, how directly relevant and necessary is this passage "
                        "for answering the user query? (1 = completely irrelevant noise, 5 = directly answers query)"
                    ),
                    "min": 1,
                    "max": 5
                }
            }
            try:
                res = router.predict(state=state, questions=questions)
                score = res.get("scores", {}).get("relevance", {}).get("score", 3)
            except Exception:
                score = 3

            candidates.append(
                SliceCandidate(
                    index=idx,
                    text=s,
                    token_count=t_count,
                    relevance_score=score,
                    is_redundant=False,
                    keep=True
                )
            )

        # 3. Budget Packer
        # Target token budget
        max_budget = int(original_tokens * (1.0 - target_reduction))
        max_budget = max(max_budget, 100)  # Safe lower bound

        # Filter out slices below minimum relevance threshold
        kept_candidates = [c for c in candidates if c.relevance_score >= min_relevance_threshold]
        
        # If too strict, fall back to top candidates
        if not kept_candidates:
            candidates.sort(key=lambda x: x.relevance_score, reverse=True)
            kept_candidates = candidates[:max(1, len(candidates) // 2)]

        # Sort by relevance density (relevance / token_count)
        kept_candidates.sort(key=lambda x: (x.relevance_score, -x.token_count), reverse=True)

        packed = []
        accumulated_tokens = 0
        for cand in kept_candidates:
            if accumulated_tokens + cand.token_count <= max_budget:
                packed.append(cand)
                accumulated_tokens += cand.token_count
            elif not packed:
                # Ensure at least the top slice is included
                packed.append(cand)
                accumulated_tokens += cand.token_count
                break

        # 4. Restore natural document reading order
        packed.sort(key=lambda x: x.index)
        optimized_context = "\n\n".join([p.text for p in packed])
        optimized_tokens = self.estimate_tokens(optimized_context)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        saved_tokens = max(0, original_tokens - optimized_tokens)
        compression_ratio = round(optimized_tokens / max(1, original_tokens), 2)

        stats = OptimizationStats(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=saved_tokens,
            compression_ratio=compression_ratio,
            slices_total=len(slices),
            slices_retained=len(packed),
            latency_ms=elapsed_ms
        )

        return OptimizationResult(
            optimized_context=optimized_context,
            stats=stats
        )
