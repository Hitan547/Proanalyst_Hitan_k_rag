# Project Report: Upwork API Technical Support RAG Bot

## 1. Objective

The goal of this project was to build a Streamlit-based technical support assistant for Upwork API documentation. The assistant needed to answer developer questions using only the provided documentation, show retrieved sources, avoid hallucinations, and integrate with a hosted Meta-Llama model through DeepInfra.

The project was designed to demonstrate:

- Python development
- RAG pipeline design
- Vector database usage
- Local embeddings
- LLM API integration
- Streamlit UI development
- secure handling of API keys
- explainable and auditable AI behavior

## 2. Final System Overview

The final app is a documentation-grounded RAG assistant. A user asks an Upwork API question, the system retrieves the top relevant documentation chunks, applies grounding checks, and then either returns a deterministic exact answer, calls the LLM with only retrieved snippets, or returns the required fallback message.

```text
User Question
     |
     v
Streamlit App
     |
     v
ChromaDB Retriever
     |
     v
Top 3 Source Chunks
     |
     v
Grounding Checks
     |
     +--> weak evidence -> fallback
     |
     v
Exact Fact Guardrails
     |
     +--> exact fact found -> direct answer
     |
     v
DeepInfra Meta-Llama
     |
     v
Answer + Sources + Scores + Latency
```

## 3. Files And Responsibilities

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface, user input, evaluation buttons, answer display, source display |
| `rag_pipeline.py` | PDF loading, chunking, embeddings, Chroma vector store, retrieval, reranking |
| `llm_client.py` | DeepInfra API call, prompt construction, latency measurement |
| `answer_guardrails.py` | Selective source-grounded answers for high-impact exact facts |
| `config.py` | Central configuration and environment variable loading |
| `evaluation.py` | Required assignment questions and evaluation-sheet questions |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example secret configuration |
| `README.md` | Setup, architecture, design decisions |
| `technical_summary.md` | Short summary for assignment submission |
| `test_cases.md` | Test cases and observed results |

## 4. Data Ingestion

The provided Upwork API PDF is stored locally in:

```text
data/upwork_api_docs.pdf
```

The PDF is loaded with LangChain's `PyPDFLoader`. After extraction, the app prints:

- total character count,
- sample text from the extracted document.

Observed document stats:

```text
Characters: 44,785
Chunks: 112
```

This sanity check is important because PDF extraction can be noisy. Technical PDFs often contain navigation text, copied website layout text, code snippets, endpoint URLs, and line breaks that do not perfectly match the original page.

## 5. Chunking Strategy

The assignment required:

```text
Chunk size: 500 characters
Overlap: 50 characters
```

I used these exact values.

The overlap matters because technical documentation often has important facts split across boundaries:

- OAuth flow descriptions
- endpoint URLs
- request parameters
- curl examples
- GraphQL schemas
- permissions and response descriptions

Without overlap, a chunk might contain the endpoint name but miss the required parameters, or contain part of an OAuth flow but lose the token validity detail.

## 6. Embeddings

The app uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Reasoning:

- runs locally,
- avoids extra embedding API cost,
- is lightweight enough for quick startup,
- works well for semantic search over technical text,
- satisfies the assignment requirement for local embeddings.

## 7. Vector Database

I used ChromaDB instead of FAISS.

Reason:

- Chroma persists embeddings locally,
- the app can restart without recomputing all embeddings,
- developer experience is better,
- it is easier to explain as a production-minded choice.

The vector database is stored in:

```text
chroma_db/
```

This folder should not be submitted unless explicitly requested because it can be rebuilt from the PDF.

## 8. Retrieval Pipeline

The retrieval system returns the top 3 chunks to match the assignment requirement.

Internally, it retrieves a wider candidate set and reranks it using:

- Chroma semantic similarity,
- lexical overlap for technical terms,
- small boosts for exact API concepts.

This helps with terms such as:

- `Authorization Code Grant`
- `Implicit Grant`
- `X-Upwork-API-TenantId`
- `MissingFieldArgument`
- `marketplaceJobPostings`
- `Service Account`
- `GraphQL`

The UI still displays only the top 3 chunks, with:

- source number,
- chunk ID,
- relevance score,
- exact snippet text.

## 9. LLM Integration

The hosted model is called through DeepInfra's OpenAI-compatible endpoint:

```text
https://api.deepinfra.com/v1/openai/chat/completions
```

Model:

```text
meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

The app uses a low temperature so answers are more factual and consistent.

Only retrieved snippets are sent to the LLM. The full PDF is not uploaded to the hosted model.

## 10. Prompt Design

The LLM prompt tells the model to:

- act as a Senior Upwork API Consultant,
- answer only from the provided snippets,
- avoid outside knowledge,
- avoid guessing,
- cite source snippets,
- return the exact fallback message when the answer is not present.

Required fallback:

```text
I'm sorry, but the provided documentation does not contain that information.
```

## 11. Hallucination Protection

The system uses multiple hallucination controls:

1. **Retrieval threshold**  
   If the best retrieval score is too weak, the app returns the fallback before calling the LLM.

2. **Evidence check**  
   Some questions, such as rate-limit questions, require exact evidence. If exact evidence is missing, the system returns the fallback.

3. **Strict system prompt**  
   The model is instructed not to guess or use outside knowledge.

4. **Selective deterministic guardrails**  
   High-impact exact facts are answered directly from source snippets when evidence is clear.

5. **Source display**  
   Users can verify every answer against exact retrieved snippets.

## 12. Deterministic Answer Guardrails

During testing, I found that the LLM sometimes made small mistakes even when retrieval was correct. For example:

- it omitted `Implicit Grant` from the OAuth grant type answer,
- it answered GraphQL error components as `errors, message, locations` instead of `message, locations, extensions`,
- it sometimes returned fallback even when broader documentation answers were present in sources.

To solve this, I improved the prompt and retrieval flow, then added a selective `answer_guardrails.py` layer for the highest-impact exact facts.

This module checks whether retrieved snippets clearly contain a small set of high-impact exact API facts. If they do, it returns a deterministic answer before calling the LLM.

This improves reliability while still staying grounded in the retrieved documentation. It does not use outside knowledge or hidden answer keys.

Examples of guarded answers:

- OAuth grant types
- GraphQL error response components
- `ValidationError (MissingFieldArgument)`
- Implicit Grant refresh-token behavior
- scopes referenced but not listed

## 13. Streamlit UI

The UI was designed to be useful for reviewers and interviewers.

It shows:

- document statistics,
- retrieval settings,
- model information,
- sanity-check sample,
- quick evaluation buttons,
- example questions,
- answer status,
- latency,
- retrieval confidence,
- number of sources used,
- exact source snippets,
- chunk IDs,
- retrieval scores.

The UI supports quick manual verification. A reviewer can ask a question, see the answer, and immediately audit the source chunks.

## 14. Issues Faced And How I Solved Them

### Issue 1: API key confusion

One key returned `401 Unauthorized`, while another key from the provided DeepInfra instructions worked. I tested keys by making a minimal chat-completion request and checking the HTTP status.

Solution:

- kept API keys in `.env`,
- never hardcoded secrets,
- used masked key endings for debugging,
- confirmed working key by checking for HTTP `200 OK`.

### Issue 2: Streamlit `set_page_config` error

Streamlit requires `st.set_page_config()` to be the first Streamlit command.

Solution:

- moved `st.set_page_config()` immediately after importing Streamlit,
- ensured config loading did not call Streamlit before page config.

### Issue 3: Streamlit secrets warning

Local development initially showed missing `secrets.toml` warnings.

Solution:

- `config.py` first checks environment variables from `.env`,
- then falls back to `st.secrets` for Streamlit Cloud.

This supports both local and deployed environments.

### Issue 4: PDF extraction noise

The PDF text contained layout artifacts, broken words, copied navigation text, and spacing issues such as:

```text
W rite
UPDA TE
V endor
```

Solution:

- added ingestion sanity check,
- used overlap during chunking,
- added lexical reranking and query expansion for technical terms,
- verified answers against retrieved source snippets.

### Issue 5: Retrieval missed exact chunks

Initial retrieval sometimes returned related chunks but missed the exact answer chunk.

Solution:

- retrieved a wider candidate pool,
- reranked candidates using semantic and lexical scoring,
- added domain-specific query expansion for exact API terminology,
- still returned only top 3 chunks in the UI.

### Issue 6: LLM over-refusal

The model sometimes returned the fallback even when the source contained the answer.

Solution:

- improved the prompt,
- added deterministic answer guardrails for exact source-supported facts.

### Issue 7: LLM partial answers

The model sometimes produced an answer that was close but incomplete.

Example:

- missed `Implicit Grant`,
- missed `extensions`,
- omitted `MissingFieldArgument`.

Solution:

- exact fact guardrails extract structured facts directly from retrieved snippets.

## 15. Evaluation Results

The system was tested against the required assignment questions and visible evaluation-sheet questions used as manual regression checks.

Final result:

```text
Required assignment questions passed
Visible sheet questions used to tune retrieval, prompting, and grounding
```

The three required assignment questions also passed:

| Question | Result |
|---|---|
| Specific request-per-second rate limit/per-key/per-IP | Correct fallback |
| OAuth access token validity | Correct: 24 hours |
| Client Credentials for private contract details | Conservative documentation-only behavior |

## 16. Why This Solution Is Explainable

Every answer can be traced to:

- retrieved chunk IDs,
- exact source snippets,
- relevance scores,
- source file metadata,
- retrieval confidence.

This makes the app easier to debug and easier to defend in an interview.

## 17. What I Would Improve With More Time

I intentionally kept the system simple because the assignment prioritizes fundamentals.

If this were expanded into a production system, I would consider:

- PDF preprocessing to remove navigation artifacts,
- automated regression tests for all evaluation questions,
- a small admin page to inspect retrieved chunks,
- optional reranking with a cross-encoder,
- better deployment observability,
- structured logs for question, chunk IDs, latency, and fallback reason.

I would avoid adding agents, memory, LangGraph, or complex multi-step workflows unless there was a real product requirement, because those would make the system harder to evaluate for this assignment.

## 18. Interview Explanation

Short explanation:

> I built a Streamlit RAG bot over the provided Upwork API documentation. The system extracts the PDF locally, chunks it into 500-character chunks with 50 overlap, embeds with local MiniLM, persists vectors in ChromaDB, retrieves the top 3 chunks, applies grounding checks and selective exact-fact guardrails, then sends only retrieved snippets to DeepInfra Meta-Llama. The UI shows the answer, latency, confidence, source snippets, chunk IDs, and scores so every response can be audited.

Key talking points:

- ChromaDB was selected for persistent local embeddings.
- MiniLM was selected for lightweight local embeddings.
- Top-3 retrieval keeps the context focused.
- Overlap protects facts spanning chunk boundaries.
- The fallback threshold reduces hallucination risk.
- Selective guardrails improve exact API fact reliability without using outside knowledge.
- The full PDF is never uploaded to the hosted LLM.
