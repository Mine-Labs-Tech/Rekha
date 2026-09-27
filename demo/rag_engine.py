"""
Demo RAG Engine: Simple, local retrieval engine simulating an existing RAG pipeline.
"""

import os
import re
from typing import List, Tuple

DOC_PATH = os.path.join(os.path.dirname(__file__), "sample_docs", "acme_policy.md")


class SimpleRAGEngine:
    def __init__(self, document_path: str = DOC_PATH):
        with open(document_path, "r", encoding="utf-8") as f:
            self.full_document = f.read()

        # Split document into chunks by section headers
        self.sections = [
            s.strip() for s in re.split(r"(?=\n##\s+)", self.full_document) if s.strip()
        ]

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve chunks matching query terms.
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        scored_sections = []
        for sec in self.sections:
            sec_words = set(re.findall(r"\w+", sec.lower()))
            overlap = len(query_words.intersection(sec_words))
            scored_sections.append((overlap, sec))

        scored_sections.sort(key=lambda x: x[0], reverse=True)
        return [sec for _, sec in scored_sections[:top_k]]

    def generate_answer(self, query: str, context_chunks: List[str]) -> str:
        """
        Synthesize answer from retrieved chunks.
        """
        joined = " ".join(context_chunks)
        query_lower = query.lower()

        if "refund" in query_lower or "cancel" in query_lower:
            return (
                "According to Acme Cloud policies, customers are eligible for a 100% money-back refund "
                "within the first 30 days of their initial subscription. After 30 days, charges are non-refundable."
            )
        elif "price" in query_lower or "cost" in query_lower or "plan" in query_lower:
            return (
                "Acme Cloud offers three plans: Starter at $49/month (5 seats), Pro at $199/month (25 seats), "
                "and Enterprise at $899/month (unlimited seats with 99.99% uptime SLA)."
            )
        elif "rate limit" in query_lower or "api" in query_lower:
            return (
                "API rate limits are: Starter at 60 req/min, Pro at 300 req/min, and Enterprise at 3,000 req/min."
            )
        else:
            return (
                f"Based on Acme Cloud documentation: {joined[:250]}..."
            )

    def execute_rag(self, query: str, namespace: str = None) -> Tuple[str, List[str]]:
        """
        Standard RAG pipeline entry point.
        Returns: (candidate_answer, retrieved_chunks)
        """
        chunks = self.retrieve(query)
        answer = self.generate_answer(query, chunks)
        return answer, chunks
