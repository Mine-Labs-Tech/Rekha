"""
Rekha: High-Performance System-1 Control Plane for Production RAG.
100% Free & Open Source under Apache-2.0.
"""

from .gateway import RekhaGateway
from .guard import GuardGate
from .cache import CacheGate
from .router import QueryRouter
from .optimizer import ContextOptimizer
from .verifier import VerificationGate
from .types import (
    RekhaPipelineResult,
    GuardResult,
    CacheResult,
    RouterResult,
    OptimizationStats,
    OptimizationResult,
    VerificationResult
)

__version__ = "0.1.1"

__all__ = [
    "RekhaGateway",
    "GuardGate",
    "CacheGate",
    "QueryRouter",
    "ContextOptimizer",
    "VerificationGate",
    "RekhaPipelineResult",
    "GuardResult",
    "CacheResult",
    "RouterResult",
    "OptimizationStats",
    "OptimizationResult",
    "VerificationResult",
]
