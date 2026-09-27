"""
Type definitions, schemas, and data structures for the Rekha Control Plane.
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Layer 1: Inbound Guard Gate Types
# ---------------------------------------------------------

class GuardResult(BaseModel):
    is_safe: bool = True
    is_prompt_injection: bool = False
    injection_confidence: float = 0.0
    contains_pii_or_secrets: bool = False
    pii_types: List[str] = Field(default_factory=list)
    toxicity_score: int = 1  # 1 (Safe) to 5 (Toxic)
    action: Literal["PASS", "MASK", "BLOCK"] = "PASS"
    reason: Optional[str] = None
    latency_ms: float = 0.0


# ---------------------------------------------------------
# Layer 2: Inbound Cache Gate Types
# ---------------------------------------------------------

class CacheResult(BaseModel):
    is_canonical: bool = False
    intent_id: Optional[str] = None
    intent_confidence: float = 0.0
    cache_hit: bool = False
    cached_payload: Optional[str] = None
    latency_ms: float = 0.0


# ---------------------------------------------------------
# Layer 3: Query Router Types
# ---------------------------------------------------------

class RouterResult(BaseModel):
    destination: Literal["BYPASS_NO_RAG", "STRUCTURED_TOOL", "VECTOR_SEARCH"] = "VECTOR_SEARCH"
    target_namespace: Optional[str] = None
    suggested_tools: List[str] = Field(default_factory=list)
    estimated_complexity: int = 1  # 1 (Trivial) to 5 (Deep)
    confidence: float = 1.0
    latency_ms: float = 0.0


# ---------------------------------------------------------
# Layer 4: Context Optimizer Types
# ---------------------------------------------------------

class SliceCandidate(BaseModel):
    index: int
    text: str
    token_count: int
    relevance_score: int = 1  # 1 to 5
    is_redundant: bool = False
    keep: bool = True


class OptimizationStats(BaseModel):
    original_tokens: int
    optimized_tokens: int
    tokens_saved: int
    compression_ratio: float
    slices_total: int
    slices_retained: int
    latency_ms: float = 0.0


class OptimizationResult(BaseModel):
    optimized_context: str
    stats: OptimizationStats


# ---------------------------------------------------------
# Layer 5: Outbound Grounding & Verification Types
# ---------------------------------------------------------

class VerificationResult(BaseModel):
    is_supported: bool = True
    alignment_score: int = 5  # 1 (Hallucination) to 5 (Strictly Grounded)
    negative_constraints_violated: List[str] = Field(default_factory=list)
    unanchored_entities: List[str] = Field(default_factory=list)
    decision: Literal["STREAM_TO_USER", "BLOCK_AND_FALLBACK", "TRIGGER_RETRY"] = "STREAM_TO_USER"
    fallback_message: Optional[str] = None
    latency_ms: float = 0.0


# ---------------------------------------------------------
# Overall Gateway Execution Result
# ---------------------------------------------------------

class RekhaPipelineResult(BaseModel):
    query: str
    final_output: str
    source: Literal["CACHE", "BLOCKED_GUARD", "RAG_VERIFIED", "RAG_FALLBACK", "DIRECT_ROUTER"]
    guard: GuardResult
    cache: CacheResult
    router: RouterResult
    optimizer: Optional[OptimizationStats] = None
    verifier: Optional[VerificationResult] = None
    total_overhead_latency_ms: float = 0.0
