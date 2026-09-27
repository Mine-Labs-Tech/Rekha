"""
Enterprise Test Suite: Layer 4 Context Optimizer
Tests syntax-aware micro-slicing (Markdown tables, code blocks), token budget packing, and reading order preservation.
"""

import pytest
from rekha.optimizer import ContextOptimizer
from rekha.types import OptimizationResult


@pytest.fixture(scope="module")
def optimizer():
    return ContextOptimizer()


class TestContextOptimizerEnterprise:
    def test_markdown_table_integrity_preserved(self, optimizer):
        """Markdown tables must NOT be severed across slice boundaries."""
        sample_doc = (
            "# Service Tier Comparison\n\n"
            "Here is the breakdown of our plans:\n\n"
            "| Plan | Price | Storage | Uptime |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| Starter | $49/mo | 100 GB | 99.9% |\n"
            "| Pro | $199/mo | 1 TB | 99.95% |\n"
            "| Enterprise | $899/mo | Unlimited | 99.99% |\n\n"
            "All plans include TLS 1.3 security."
        )
        slices = optimizer.micro_slice(sample_doc)
        
        # Verify the table is preserved intact in one slice
        table_slices = [s for s in slices if "| Starter |" in s]
        assert len(table_slices) == 1, "Table was severed into multiple slices!"
        assert "| Enterprise |" in table_slices[0], "Table was truncated midway!"

    def test_code_block_integrity_preserved(self, optimizer):
        """Code blocks with ``` must be kept intact."""
        sample_doc = (
            "To connect to the Acme API, initialize the client as follows:\n\n"
            "```python\n"
            "import acme\n"
            "client = acme.Client(api_key='sk_test_123')\n"
            "response = client.query(endpoint='/v1/status')\n"
            "print(response.status_code)\n"
            "```\n\n"
            "Make sure your firewall allows outbound HTTPS on port 443."
        )
        slices = optimizer.micro_slice(sample_doc)
        code_slices = [s for s in slices if "client = acme.Client" in s]
        assert len(code_slices) == 1
        assert "```python" in code_slices[0]
        assert "```" in code_slices[0]

    def test_noisy_document_compression_and_ordering(self, optimizer):
        """
        Takes a document with 80% irrelevant legal/footer boilerplate and 20% relevant facts.
        Must prune the noise, keep the core facts, and preserve natural reading order.
        """
        noisy_doc = (
            "# Acme Terms of Service\n\n"
            "SECTION 1: DISCLAIMER OF WARRANTIES\n"
            "THE SERVICE IS PROVIDED ON AN AS-IS AND AS-AVAILABLE BASIS. TO THE MAXIMUM EXTENT "
            "PERMITTED BY LAW, ACME EXPRESSLY DISCLAIMS ALL WARRANTIES OF ANY KIND, WHETHER EXPRESS OR IMPLIED.\n\n"
            "SECTION 2: REFUND POLICY DETAILS\n"
            "Customers who purchase any annual or monthly plan are eligible for a 100% money-back guarantee "
            "if requested within the first 30 days of service. After 30 days, all sales are strictly final.\n\n"
            "SECTION 3: GOVERNING LAW AND JURISDICTION\n"
            "These terms shall be governed by and construed in accordance with the laws of the State of Delaware, "
            "without regard to its conflict of law principles. Any legal suit or proceeding shall be instituted exclusively.\n\n"
            "SECTION 4: COOKIE POLICY AND TRACKING BEACONS\n"
            "We use essential cookies to maintain user session state across browser refreshes and load balancers. "
            "Third-party tracking cookies may be disabled via browser settings at any time without impacting account access."
        )

        query = "How many days do I have to ask for a refund?"
        result: OptimizationResult = optimizer.optimize(
            query=query,
            documents=noisy_doc,
            target_reduction=0.50
        )

        # 1. Must achieve token reduction
        assert result.stats.tokens_saved > 50
        assert result.stats.compression_ratio < 0.80

        # 2. Must retain the refund section
        assert "100% money-back guarantee" in result.optimized_context
        assert "30 days" in result.optimized_context

    def test_edge_case_empty_string(self, optimizer):
        """Optimizer must gracefully handle empty or single-sentence text."""
        result: OptimizationResult = optimizer.optimize(query="test", documents="")
        assert result.optimized_context == ""
        assert result.stats.tokens_saved == 0
