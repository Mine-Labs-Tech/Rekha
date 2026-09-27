# REKHA

<p align="center">
  <a href="https://pypi.org/project/minelabs-rekha/"><img src="https://img.shields.io/pypi/v/minelabs-rekha.svg?color=blue" alt="PyPI version" /></a>
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License: Apache 2.0" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Latency-Sub--35ms-brightgreen.svg" alt="Sub-35ms Latency" />
  <img src="https://img.shields.io/badge/API_Keys-Zero_Required-orange.svg" alt="Zero API Keys" />
  <img src="https://img.shields.io/badge/Deployment-100%25_Air--Gapped-success.svg" alt="100% Air-Gapped" />
</p>

<h3 align="center">
  <b>The High-Performance System-1 Control Plane for Production RAG</b>
</h3>

<p align="center">
  Cut LLM token bills by 50%+, block prompt injections in ~35ms, and audit hallucinations before streaming—using a single Python decorator. Zero external API calls, zero migration friction, 100% free and open-source.
</p>

<p align="center">
  <a href="landing/index.html"><b>🌐 Interactive Landing Page</b></a> •
  <a href="landing/docs.html"><b>📖 Documentation & Cookbook</b></a> •
  <a href="Architecture.md"><b>🏗️ Technical Architecture</b></a> •
  <a href="BENCHMARK_REPORT.md"><b>📊 Benchmark Report</b></a> •
  <a href="#-what-makes-rekha-different-from-competitors"><b>🥊 Competitor Teardown</b></a>
</p>

---

## ⚡ The Core USP (Unique Selling Proposition)

> **"Rekha is the first zero-latency, 100% open-source System-1 control plane that wraps around any existing RAG pipeline in 1 line of code—cutting token bills by 50%, blocking prompt injections in 35ms, and preventing hallucinations with zero external API keys."**

### Why Developers Choose Rekha:
1. **Zero Migration Friction (The 1-Line Decorator):** You don't re-index your vector database, you don't migrate embeddings, and you don't rewrite your prompts. Just add `@gateway.protect`.
2. **Sub-35ms Non-Autoregressive Determinism:** Rekha doesn't use a slow generative LLM to police another LLM. It uses a mathematical non-autoregressive encoder (`Choice`, `Score`, `Noul`) that evaluates decisions in ~35ms and physically cannot be hijacked by prompt injections.
3. **100% Air-Gapped & Free:** Zero cloud telemetry, zero API keys, zero dollars spent. Your proprietary data never leaves your local CPU or GPU.
4. **The Latency Paradox:** By pruning 50%+ of noisy context tokens before prompt dispatch, downstream LLM generation begins **~800ms earlier**, making your entire RAG pipeline **~620ms faster overall**.

---

## 🏗️ Architecture: The 5-Layer Sandwich Control Plane

```
                    ┌────────────────────────────────────────────────────────┐
                    │                      REKHA GATEWAY                     │
User Query ────────►│                                                        │
                    │  [ INBOUND STAGE ]                                     │
                    │  1. Inbound Guard Gate   (Jailbreak, PII, Policy: ~37ms)│
                    │  2. Smriti Gate          (Canonical Intent Cache: <5ms)│
                    │  3. Disha Router         (Bypass / SQL / Vector: ~38ms)│
                    │                                                        │
                    │  [ RETRIEVAL STAGE ]                                   │
                    │  4. Samkshep Slicer      (Syntax-Safe Pruning -54%: ~69ms)
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │     EXISTING RAG      │
                                    │  (100% Untouched)     │
                                    │  Vector DB  │   LLM   │
                                    └───────────┬───────────┘
                                                │
                    ┌───────────────────────────┴────────────────────────────┐
                    │  [ OUTBOUND STAGE ]                                    │
                    │  5. Satya Praman Gate    (Entity Anchors, Negative     │
                    │                           Constraints, Grounding: ~72ms│
                    │                                                        │
                    │  Decision:  [ SUPPORTED ]   ──► Stream to User         │
                    │             [ BLOCK/RETRY ] ──► Fallback / Regenerate  │
                    └────────────────────────────────────────────────────────┘
```

---

## ⏱️ Live Response Times (Empirically Measured on Local CPU/GPU)

| Layer | Component Name | Function / Decision | Response Time | vs. LLM-Prompt Guardrails |
| :--- | :--- | :--- | :---: | :--- |
| **Layer 1** | **Inbound Guard Gate** | Evaluates prompt injections, jailbreaks, PII & toxicity | **~37 ms** | **~80x faster** than calling GPT-4o (2,500ms) |
| **Layer 2** | **Smriti Gate** | Canonical Intent Clustering + local memory LRU/TTL | **&lt;5 ms (Hit)** | **~90x faster** than a full Vector DB + LLM call |
| **Layer 3** | **Disha Router** | Categorizes `BYPASS`, `STRUCTURED_TOOL`, or `VECTOR` | **~38 ms** | **~75x faster** than LLM tool routers |
| **Layer 4** | **Samkshep Slicer** | Micro-slicing + parallel batch scoring + knapsack packing | **~69 ms** | Slices 50%+ noise in memory (preserves tables) |
| **Layer 5** | **Satya Praman** | Entity anchor audit ($ / dates / %) + negative constraints | **~72 ms** | Replaces 3-second LLM-as-a-judge evals |

> **The Net Latency Paradox:** Rekha adds ~180ms of total control overhead on full RAG, but because Samkshep prunes 50%+ of input tokens, the downstream LLM streams its first token **800ms faster**. **Net result: The user gets their answer ~620ms FASTER.**

---

## 📦 Installation

Rekha is published on PyPI as `minelabs-rekha`. It runs **100% locally and offline**—it does not require any API keys, tokens, or external network connections:

```bash
pip install minelabs-rekha
```

> **Note on Imports:** Regardless of the PyPI distribution name, the Python package imports cleanly as `rekha`:
> ```python
> import rekha
> from rekha import RekhaGateway
> ```

---

## 🚀 60-Second Quickstart

Add protection to your existing RAG pipeline in 2 lines:

```python
import openai
from rekha import RekhaGateway

# 1. Initialize the Gateway (loads local weights once)
gateway = RekhaGateway(
    target_context_reduction=0.50,  # Prune 50% of context noise
    negative_constraints=[
        "Do not disclose internal employee compensation.",
        "Do not promise discounts higher than 15%."
    ]
)

# 2. Decorate your existing RAG query function
@gateway.protect
def my_rag_pipeline(user_query: str):
    chunks = vector_db.similarity_search(user_query, k=5)
    context = "\n\n".join([c.page_content for c in chunks])
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Answer based on:\n{context}"},
            {"role": "user", "content": user_query}
        ]
    )
    return response.choices[0].message.content, context

# 3. Call your function as usual
result = my_rag_pipeline("What are our SLA response times for Tier-1 outages?")

print("Final Output:", result.final_output)
print("Execution Source:", result.source)          # "CACHE", "RAG_VERIFIED", or "BLOCKED_GUARD"
print("Control Overhead:", result.total_overhead_latency_ms, "ms")
```

---

## 🍳 Production Framework Cookbook

### 1. LangChain & LangGraph
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

### 2. LlamaIndex
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

### 3. FastAPI Service with Production Headers
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
    
    # Emit observability headers
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

## 🥊 What Makes Rekha Different From Competitors?

| Competitor Category | Key Players | How They Work | Why Rekha is Radically Better |
| :--- | :--- | :--- | :--- |
| **Prompt Compressors** | **Microsoft LLMLingua** | Token-level perplexity dropping via small causal models. | **LLMLingua destroys syntax:** Deletes closing brackets `}`, corrupts tables/JSON, and drops words like *"not"*. <br>👉 **Rekha preserves syntax:** Micro-slicer protects Markdown tables, code blocks, and natural reading order. |
| **AI Guardrails** | **Nvidia NeMo / Guardrails AI** | Uses Colang rules or calls secondary LLMs to check safety. | **Too slow & expensive:** Calling a second LLM adds 2–4 seconds of latency and doubles API bills. <br>👉 **Rekha blocks injections in ~35ms** locally for $0.00 without generative lag. |
| **Document Rerankers** | **Cohere Rerank / BGE** | Reorders retrieved chunks by relevance score. | **Does not compress or verify:** If a top chunk has 1,000 tokens with only 1 useful sentence, you still pay for all 1,000 tokens. <br>👉 **Rekha prunes the noise inside the chunks** and audits output facts before delivery. |
| **Evaluation / Grounding** | **Ragas / TruLens** | Calls GPT-4o ("LLM-as-a-judge") to grade answers against context. | **Unusable on live user traffic:** Taking 3 seconds to verify an answer kills live chat UX. <br>👉 **Rekha verifies negative constraints & numbers in ~70ms** before streaming. |
| **Semantic Caches** | **Redis LangCache / GPTCache** | Cosine distance thresholds over 1536d vector embeddings. | **Threshold Drift:** Small distance differences cause "How do I cancel?" to falsely match "How do I upgrade?". <br>👉 **Rekha uses discrete Canonical Intent Clustering**, yielding 99%+ deterministic confidence matches. |

---

## 🐳 Air-Gapped Production Deployment

For enterprise VPCs with zero outbound internet access, pre-bake the model weights into your container image:

```dockerfile
FROM python:3.10-slim
WORKDIR /app

# Install package
RUN pip install --no-cache-dir minelabs-rekha fastapi uvicorn

# Pre-cache local weights into image during build
ENV REKHA_OFFLINE_MODE=1
RUN python -c "from rekha import RekhaGateway; RekhaGateway()"

COPY . /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📂 Repository Structure

```
rekha/
├── rekha/                     # Core Python Package (Apache-2.0)
│   ├── __init__.py            # Package entrypoint & public exports
│   ├── gateway.py             # RekhaGateway orchestrator & @protect decorator
│   ├── guard.py               # Layer 1: Inbound Guard Gate (Injection, PII, Toxicity)
│   ├── cache.py               # Layer 2: Smriti Gate (Canonical Intent Clustering)
│   ├── router.py              # Layer 3: Disha Router (Query Dispatcher)
│   ├── optimizer.py           # Layer 4: Samkshep Slicer (Context Optimizer)
│   ├── verifier.py            # Layer 5: Satya Praman (Outbound Grounding Auditor)
│   └── types.py               # Pydantic v2 data models & decision contracts
│
├── landing/                   # Sleek Obsidian Web Interface
│   ├── index.html             # High-conversion interactive landing page
│   └── docs.html              # Comprehensive technical docs & framework cookbook
│
├── tests/                     # 25-Stage Automated Enterprise Test Suite (pytest)
├── Architecture.md            # Mathematical specifications & layer deep-dives
├── BENCHMARK_REPORT.md        # Comprehensive evaluation report
├── Plan.md                    # Strategic roadmap & competitor teardown
├── pyproject.toml             # Build & packaging configuration
└── README.md                  # Project documentation
```

---

## 📜 License

Distributed under the **Apache-2.0 License**. Free for personal, commercial, and enterprise production deployments with zero restrictions.
