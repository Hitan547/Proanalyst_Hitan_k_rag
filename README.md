# Upwork API Technical Support RAG Bot

<div align="center">

**A source-grounded Streamlit RAG assistant for Upwork API documentation, built with local embeddings, persistent ChromaDB retrieval, DeepInfra Meta-Llama, and selective exact-fact guardrails.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white)](https://proanalysthitank-p9xvkrnqrj9ahyey5xmh3a.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=white)](runtime.txt)
[![Vector DB](https://img.shields.io/badge/Vector%20DB-ChromaDB-5b61ff?style=for-the-badge)](https://www.trychroma.com/)
[![LLM](https://img.shields.io/badge/LLM-DeepInfra%20Meta--Llama-green?style=for-the-badge)](https://deepinfra.com/)

*Ask Upwork API questions, get answers grounded in retrieved documentation snippets, and audit every response through sources, chunk IDs, scores, latency, and confidence.*

</div>

---

## Live Demo

The deployed Streamlit app is available here:

[https://proanalysthitank-p9xvkrnqrj9ahyey5xmh3a.streamlit.app/](https://proanalysthitank-p9xvkrnqrj9ahyey5xmh3a.streamlit.app/)

## What This Project Does

This project implements a technical support bot for the provided Upwork API documentation. It follows the assignment requirements closely while adding lightweight production-minded polish:

- local PDF ingestion,
- exact 500-character chunking with 50-character overlap,
- local MiniLM embeddings,
- persistent ChromaDB storage,
- top-3 retrieval,
- DeepInfra Meta-Llama generation,
- source snippets,
- latency display,
- retrieval confidence,
- hallucination fallback,
- selective guardrails for high-impact exact API facts.

The goal is not to build an unnecessarily complex agent system. The goal is to build a reliable, explainable, source-grounded RAG application that can be reviewed and defended line by line.

## Evaluation Result

The final system was checked against the required assignment questions and representative visible evaluation-sheet questions.

| Evaluation Set | Result |
|---|---:|
| Required assignment questions | 3 / 3 pass |
| Visible evaluation-sheet questions | Used for manual regression checks |
| Negative hallucination-trap questions | Correct fallback |
| Source traceability | Chunk IDs, snippets, and scores shown in UI |

Examples of expected behavior:

| Question Type | Final Behavior |
|---|---|
| OAuth access token TTL | Returns 24 hours and `expires_in: 86400` seconds |
| OAuth grant types | Returns Authorization Code, Implicit, Client Credentials, Refresh Token |
| GraphQL bad requests | Returns HTTP 200 OK with errors in response body |
| Missing required GraphQL argument | Returns `ValidationError` / `MissingFieldArgument` |
| Rate limit not present in docs | Returns required fallback message |

## Key Capabilities

| Capability | Implementation | Why It Matters |
|---|---|---|
| Local document ingestion | `PyPDFLoader` loads the provided PDF locally | Full document is not uploaded to the hosted LLM |
| Required chunking | 500 characters, 50 overlap | Preserves OAuth flows, URLs, parameters, and GraphQL context |
| Local embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Fast, lightweight, no embedding API cost |
| Persistent vector DB | ChromaDB persisted to `chroma_db/` | Avoids recomputing embeddings after restart |
| Top-3 retrieval | Semantic retrieval plus lexical reranking | Keeps context focused and auditable |
| Source traceability | Chunk IDs, scores, snippets | Reviewers can verify every answer |
| Hallucination guard | Threshold + evidence checks + strict fallback | Prevents weak matches from becoming guessed answers |
| Selective exact-fact guardrails | `answer_guardrails.py` | Prevents LLM omissions on high-impact OAuth and GraphQL facts |
| Hosted LLM | DeepInfra Meta-Llama OpenAI-compatible API | Generates concise answers from retrieved snippets only |
| Streamlit UI | Answer, confidence, latency, sources | Simple reviewer-friendly demo |

## Architecture

```text
Provided Upwork API PDF
        |
        v
Local PDF extraction
        |
        v
Sanity check
character count + sample text
        |
        v
500-character chunks
50-character overlap
        |
        v
Local MiniLM embeddings
        |
        v
Persistent ChromaDB vector store
        |
        v
Semantic retrieval + lexical reranking
        |
        v
Top 3 source chunks
        |
        v
Retrieval threshold + evidence checks
        |
        +--> weak evidence -> required fallback
        |
        v
Selective exact-fact guardrails
        |
        +--> exact source-supported fact -> direct answer
        |
        v
DeepInfra Meta-Llama
retrieved snippets only
        |
        v
Streamlit UI
answer + latency + confidence + sources
```

## RAG Pipeline

1. Load `data/upwork_api_docs.pdf` locally.
2. Print total character count and sample extracted text.
3. Split into 500-character chunks with 50-character overlap.
4. Add metadata: `chunk_id` and `source_file`.
5. Embed chunks locally with `all-MiniLM-L6-v2`.
6. Store vectors in persistent ChromaDB.
7. Retrieve a wider candidate set and rerank with semantic and lexical signals.
8. Return the top 3 chunks to the app.
9. Apply retrieval threshold and evidence checks.
10. Apply selective guardrails for high-impact exact API facts.
11. If no direct guardrail answer exists, call DeepInfra Meta-Llama with retrieved snippets only.
12. Display answer, latency, confidence, source snippets, chunk IDs, and scores.

## Project Structure

```text
Proanalyst/
app.py                    # Streamlit UI and app flow
rag_pipeline.py           # PDF loading, chunking, embeddings, Chroma retrieval
llm_client.py             # DeepInfra OpenAI-compatible chat client
answer_guardrails.py      # Deterministic source-grounded exact answers
config.py                 # Environment variables and constants
evaluation.py             # Required and sheet evaluation questions
requirements.txt          # Python dependencies
runtime.txt               # Streamlit Cloud Python version
.env.example              # Example secret configuration
README.md                 # Main project documentation
data/
  upwork_api_docs.pdf     # Provided Upwork API documentation
docs/
  PROJECT_REPORT.md       # Detailed implementation report
  technical_summary.md    # Assignment technical summary
  test_cases.md           # Evaluation and test results
```

## Documentation

- [Project Report](docs/PROJECT_REPORT.md): detailed implementation story, architecture, challenges, fixes, and interview talking points.
- [Technical Summary](docs/technical_summary.md): concise assignment-ready technical summary.
- [Test Cases](docs/test_cases.md): required tests, expected behavior, and final evaluation results.

## Quick Start

```bash
git clone https://github.com/Hitan547/Proanalyst_Hitan_k.git
cd Proanalyst_Hitan_k
pip install -r requirements.txt
streamlit run app.py
```

Create a local `.env` file:

```env
DEEPINFRA_API_KEY=your_deepinfra_key_here
DEEPINFRA_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

Windows virtual environment command used during development:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Open:

```text
http://localhost:8501
```

## Streamlit Cloud Deployment

This repo includes `runtime.txt`:

```text
python-3.10
```

This is important because newer Python versions can force some dependencies to build from source on Streamlit Cloud.

Add secrets in Streamlit Cloud:

```toml
DEEPINFRA_API_KEY = "your_key_here"
DEEPINFRA_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
```

Do not commit `.env` or any real API key.

## Design Decisions

**Why ChromaDB instead of FAISS?**  
ChromaDB persists embeddings locally, so the app can restart without rebuilding all vectors. This improves startup time and makes the system more production-minded.

**Why MiniLM?**  
`all-MiniLM-L6-v2` is lightweight, local, fast, and suitable for semantic retrieval over focused technical documentation.

**Why top 3 chunks?**  
Top-3 retrieval provides enough context for most answers while limiting noise and token usage.

**Why selective guardrails?**  
For high-impact exact facts, LLMs can be slightly inconsistent. The guardrails return source-supported answers for cases such as token TTLs, OAuth grant types, OAuth endpoints, GraphQL error fields, and documented gaps such as missing scope names.

**Why not add agents or memory?**  
The assignment asked for a focused RAG bot. I intentionally avoided extra agent frameworks, memory, and unrelated complexity so the solution stays simple, auditable, and easy to evaluate.

## Security

- API keys are loaded from `.env` locally or Streamlit secrets in deployment.
- `.env` is ignored by Git.
- The full PDF is processed locally.
- Only the top retrieved snippets are sent to the hosted LLM.
- Chunk scores and IDs are shown in the UI but not sent as hidden answer keys.

## Submission Checklist

Included:

- `app.py`
- `rag_pipeline.py`
- `llm_client.py`
- `answer_guardrails.py`
- `config.py`
- `evaluation.py`
- `requirements.txt`
- `runtime.txt`
- `.env.example`
- `README.md`
- `docs/PROJECT_REPORT.md`
- `docs/technical_summary.md`
- `docs/test_cases.md`
- `data/upwork_api_docs.pdf`

Excluded:

- `.env`
- `.venv/`
- `chroma_db/`
- `instruction_review/`
- `exact_rag_answers.*`
- `sheet_eval_results.json`
- `__pycache__/`

## Interview Summary

> I built a Streamlit RAG bot over the provided Upwork API documentation. It extracts the PDF locally, chunks it into 500-character chunks with 50 overlap, embeds locally with MiniLM, persists vectors in ChromaDB, retrieves the top 3 chunks, applies grounding checks and selective exact-fact guardrails, then sends only retrieved snippets to DeepInfra Meta-Llama. The UI shows answer status, latency, confidence, source snippets, chunk IDs, and scores so every response is auditable.
