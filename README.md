# Rekha - High-Performance System-1 Control Plane and Gateway for Production RAG

<p align="center">
  <a href="https://pypi.org/project/minelabs-rekha/"><img src="https://img.shields.io/pypi/v/minelabs-rekha.svg?color=blue" alt="PyPI version" /></a>
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License: Apache 2.0" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Latency-Sub--35ms-brightgreen.svg" alt="Sub-35ms Latency" />
  <img src="https://img.shields.io/badge/Air--Gapped-Zero_API_Keys-success.svg" alt="Air-Gapped" />
</p>

<p align="center">
  <b>Sub-35ms non-autoregressive control plane for production RAG systems.</b><br>
  Intercepts prompt injections, caches recurring intents, prunes 50%+ context noise, and audits hallucinations with zero external API dependencies.
</p>

<p align="center">
  <a href="landing/index.html">Overview</a> •
  <a href="landing/docs.html">Documentation & Recipes</a> •
  <a href="Architecture.md">Architecture Specification</a> •
  <a href="BENCHMARK_REPORT.md">Benchmarks</a>
</p>

---

## Overview

Rekha is an open-source, deterministic **System-1 control plane** designed to wrap around existing Retrieval-Augmented Generation (RAG) pipelines without modifying vector databases, embedding models, or system prompts.

Rather than invoking expensive secondary LLMs (which introduce 1,500ms–3,000ms latency and generative vulnerabilities), Rekha executes multi-predicate decision boundaries in **sub-35ms** using local non-autoregressive encoder backbones.

### Key Capabilities

- **Inbound Security Gate:** Detects prompt injections, jailbreaks, and scrubs sensitive PII (credit cards, SSNs, tokens) deterministically in ~37ms.
- **Canonical Intent Cache (Smriti):** Resolves recurring questions in &lt;5ms without querying vector indices or downstream LLMs.
- **Query Router (Disha):** Routes conversational queries and structured SQL lookups in ~38ms, avoiding unnecessary vector database searches.
- **Context Optimizer (Samkshep):** Micro-slices retrieved chunks into atomic semantic units, preserving Markdown tables and code syntax while pruning 50%–60% of noise tokens.
- **Outbound Grounding Auditor (Satya Praman):** Validates entity anchors (currency, dates, percentages) and enforces negative policy constraints in ~72ms before streaming responses.
- **The Latency Paradox:** Removing 50%+ noise tokens reduces LLM time-to-first-token (TTFT) by ~800ms. Despite the ~180ms control plane overhead, total end-to-end latency is **~620ms faster**.

---

## Installation

```bash
pip install minelabs-rekha
```

Rekha runs 100% locally and offline. It requires zero API keys or external network connections during inference.

---

## Quickstart

Add Rekha to any existing RAG pipeline using the `@gateway.protect` decorator:

```python
import openai
from rekha import RekhaGateway

# Initialize gateway (loads local encoder weights once)
gateway = RekhaGateway(
    target_context_reduction=0.50,
    negative_constraints=[
        "Do not disclose internal compensation policies.",
        "Do not offer unapproved discounts."
    ]
)

@gateway.protect
def query_rag(query: str):
    chunks = vector_db.similarity_search(query, k=5)
    context = "\n\n".join([c.page_content for c in chunks])

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Answer using:\n{context}"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content, context

# Execute pipeline
result = query_rag("What are our SLA terms for Tier-1 outages?")

print("Response:", result.final_output)
print("Source:", result.source)                         # CACHE, RAG_VERIFIED, or BLOCKED_GUARD
print("Overhead Latency:", result.total_overhead_latency_ms, "ms")
```

---

## Execution Pipeline

```
User Query ──► [ INBOUND STAGE ]
                 ├── Layer 1: Inbound Guard Gate   (Jailbreak & PII Filter: ~37ms)
                 ├── Layer 2: Smriti Gate          (Canonical Intent Cache: <5ms)
                 └── Layer 3: Disha Router         (Bypass / SQL / Vector: ~38ms)
                                     │
                                     ▼
               [ RETRIEVAL STAGE ]
                 └── Layer 4: Samkshep Slicer      (Syntax-Safe Pruning -54%: ~69ms)
                                     │
                                     ▼
               [ EXISTING PIPELINE ] ──► Vector DB ──► Model (GPT-4o, Claude)
                                     │
                                     ▼
               [ OUTBOUND STAGE ]
                 └── Layer 5: Satya Praman Gate    (Entity Anchor Audit: ~72ms)
                                     │
                                     ▼
                               Stream to User
```

### Layer Latency Profile

| Stage | Name | Target Function | Measured Latency |
| :--- | :--- | :--- | :---: |
| **01** | **Inbound Guard** | Evaluates prompt injections, jailbreaks, and PII masking | **~37 ms** |
| **02** | **Smriti Gate** | Canonical intent clustering + local LRU cache | **&lt;5 ms (Hit)** |
| **03** | **Disha Router** | Dispatches to `BYPASS`, `STRUCTURED_TOOL`, or `VECTOR` | **~38 ms** |
| **04** | **Samkshep Slicer** | Parallel sentence scoring & knapsack packing | **~69 ms** |
| **05** | **Satya Praman** | Entity anchor audit ($ / dates) & policy compliance | **~72 ms** |

---

## Framework Integrations

### LangChain & LangGraph

```python
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from rekha import RekhaGateway

gateway = RekhaGateway(target_context_reduction=0.55)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

@gateway.protect
def run_langchain_pipeline(query: str):
    docs = retriever.get_relevant_documents(query)
    context_str = "\n\n".join([d.page_content for d in docs])
    prompt = f"Context:\n{context_str}\n\nQuestion: {query}"
    response = llm.invoke(prompt)
    return response.content, context_str
```

### LlamaIndex

```python
from llama_index.core import VectorStoreIndex
from rekha import RekhaGateway

gateway = RekhaGateway()
query_engine = index.as_query_engine(similarity_top_k=6)

@gateway.protect
def llamaindex_query(query_text: str):
    response = query_engine.query(query_text)
    context = "\n\n".join([n.node.get_content() for n in response.source_nodes])
    return str(response), context
```

### FastAPI Production Service

```python
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from rekha import RekhaGateway

app = FastAPI(title="Enterprise RAG Service")
gateway = RekhaGateway()

class ChatRequest(BaseModel):
    query: str

@app.post("/v1/chat")
async def chat_endpoint(req: ChatRequest, response: Response):
    result = gateway.execute(query=req.query, rag_executor=my_internal_rag_worker)

    response.headers["X-Rekha-Latency-Ms"] = str(round(result.total_overhead_latency_ms, 2))
    response.headers["X-Rekha-Source"] = result.source

    if result.source == "BLOCKED_GUARD":
        raise HTTPException(status_code=400, detail=result.final_output)

    return {
        "response": result.final_output,
        "source": result.source,
        "tokens_pruned": result.optimizer.pruning_ratio if result.optimizer else 0.0
    }
```

---

## Comparison with Alternatives

| Category | Point Solution | Common Limitations | Rekha Advantage |
| :--- | :--- | :--- | :--- |
| **Context Pruning** | LLMLingua | Token-level perplexity drops corrupt tables, JSON, and negation tokens. | **Syntax-Safe Micro-Slicing:** Evaluates complete sentence units; preserves Markdown tables and code. |
| **Guardrails** | NeMo / Guardrails AI | Generative checks add 2,000ms–4,000ms latency and double LLM bills. | **Sub-35ms Non-Autoregressive:** Evaluates binary classification heads locally with zero API cost. |
| **Rerankers** | Cohere / BGE | Reorders chunks without pruning internal chunk noise. | **In-Chunk Pruning:** Discards irrelevant sentences inside retrieved chunks, saving 50%+ tokens. |
| **Evaluation** | Ragas / TruLens | Asynchronous or batch evaluation; too slow for live chat streaming. | **In-Flight Grounding:** Audits exact entity anchors ($ / dates / %) in ~72ms before stream delivery. |
| **Semantic Cache** | Redis LangCache | Cosine similarity thresholds drift, causing false-positive matches. | **Canonical Intent Clustering:** Discrete cluster mapping guarantees high-confidence FAQ cache hits. |

---

## Air-Gapped Deployment

For secure environments with zero external network access, pre-cache model weights in your container image during build:

```dockerfile
FROM python:3.10-slim
WORKDIR /app

RUN pip install --no-cache-dir minelabs-rekha fastapi uvicorn

# Pre-cache weights into image during build
ENV REKHA_OFFLINE_MODE=1
RUN python -c "from rekha import RekhaGateway; RekhaGateway()"

COPY . /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## License

Rekha is distributed under the **Apache-2.0 License**. Free for personal, commercial, and enterprise production deployments with zero restrictions.
