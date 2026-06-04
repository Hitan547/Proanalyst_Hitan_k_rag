# Upwork API Technical Support RAG Bot

A Streamlit technical-support assistant that answers questions about the provided Upwork API documentation using a local RAG pipeline. The application extracts text from the local PDF, creates local embeddings, retrieves the most relevant chunks with ChromaDB, and sends only the selected snippets to DeepInfra Meta-Llama for grounded answer generation.

The system is intentionally simple, auditable, and aligned with the assignment requirements.

## Features

- Local PDF ingestion from `data/upwork_api_docs.pdf`
- Sanity check with character count and sample extracted text
- 500-character chunks with 50-character overlap
- Local embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Persistent ChromaDB vector store
- Top-3 retrieval with chunk IDs and relevance scores
- Retrieval threshold fallback to reduce hallucinations
- Deterministic answer guardrails for exact API facts
- DeepInfra Meta-Llama chat completion integration
- Streamlit UI with answer, latency, confidence, and sources
- Evaluation buttons for the required assignment test cases
- Environment-variable based API key loading

## Architecture

```text
Provided Upwork API PDF
        |
        v
Local PDF text extraction
        |
        v
Sanity check
characters + sample text
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
Top-3 semantic retrieval
        |
        v
Retrieval threshold + evidence checks
        |
        +--> weak evidence -> required fallback message
        |
        v
Deterministic exact-fact guardrails
        |
        +--> exact API fact found -> direct grounded answer
        |
        v
DeepInfra Meta-Llama
retrieved snippets only
        |
        v
Streamlit UI
answer + latency + confidence + sources
```

## Project Structure

```text
Proanalyst/
├── app.py                    # Streamlit UI and app flow
├── rag_pipeline.py           # PDF loading, chunking, embeddings, Chroma retrieval
├── llm_client.py             # DeepInfra OpenAI-compatible chat client
├── answer_guardrails.py      # Deterministic answers for exact grounded facts
├── config.py                 # Environment/config values
├── evaluation.py             # Required and sheet evaluation questions
├── requirements.txt          # Python dependencies
├── .env.example              # Example secret configuration
├── README.md                 # Setup and architecture
├── technical_summary.md      # Short submission summary
├── test_cases.md             # Evaluation results
├── PROJECT_REPORT.md         # Detailed implementation report
└── data/
    └── upwork_api_docs.pdf   # Provided documentation
```

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` from `.env.example`:

```env
DEEPINFRA_API_KEY=your_deepinfra_key_here
DEEPINFRA_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

3. Run the app:

```bash
streamlit run app.py
```

Windows virtual environment command used during development:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

4. Open:

```text
http://localhost:8501
```

## How The RAG Pipeline Works

1. `rag_pipeline.py` loads the local PDF using `PyPDFLoader`.
2. It prints the total character count and a sample of extracted text for ingestion verification.
3. The document is split into 500-character chunks with 50-character overlap.
4. Each chunk receives metadata:
   - `chunk_id`
   - `source_file`
5. `all-MiniLM-L6-v2` creates local embeddings.
6. ChromaDB stores embeddings persistently in `chroma_db/`.
7. Retrieval gets a wider candidate set, reranks using semantic and lexical signals, and returns the top 3 chunks.
8. The app checks retrieval strength and required evidence before calling the LLM.
9. Exact API/list questions are answered by deterministic guardrails when the retrieved sources clearly contain the fact.
10. Otherwise, DeepInfra Meta-Llama generates an answer using only retrieved snippets.

## Design Decisions

**Why ChromaDB?**  
ChromaDB persists embeddings locally, so after the first indexing run the app does not need to recompute embeddings on every restart. This improves startup time and makes the app more production-minded than rebuilding vectors every run.

**Why MiniLM?**  
`sentence-transformers/all-MiniLM-L6-v2` runs locally, is lightweight, avoids embedding API cost, and performs well for semantic retrieval over technical documentation.

**Why 500 characters and 50 overlap?**  
The assignment required these values. The overlap helps preserve context when OAuth flows, endpoint URLs, curl examples, request parameters, or GraphQL schemas span chunk boundaries.

**Why top 3 chunks?**  
Top-3 retrieval balances evidence and noise. It provides enough context to answer most API questions without giving the model too much irrelevant text.

**Why deterministic guardrails?**  
Some questions ask for exact API facts, such as grant types, GraphQL error fields, or subscription entity types. The LLM can occasionally omit an item or over-refuse even when the source contains the answer. `answer_guardrails.py` fixes this by returning exact answers only when the retrieved snippets clearly contain the required evidence.

**Why retrieval threshold?**  
Even unrelated questions retrieve something from a vector database. The threshold and evidence checks prevent weak matches from becoming hallucinated answers.

## Prompting And Safety

The LLM receives:

- only retrieved snippets,
- no full document upload,
- no API keys,
- no chunk scores,
- no hidden answer key.

The system prompt instructs the model to answer only from snippets and use the required fallback:

```text
I'm sorry, but the provided documentation does not contain that information.
```

## Evaluation

The system was checked against 36 visible evaluation-sheet questions.

Result after retrieval tuning and guardrails:

```text
Matches expected meaning: 36 / 36
Unresolved issues: 0
```

Required assignment questions:

| Question | Expected Behavior | Result |
|---|---|---|
| Specific request-per-second rate limit/per-key/per-IP | Fallback because not present in docs | Pass |
| OAuth access token validity | 24 hours / 86400 seconds | Pass |
| Client Credentials for user's private contract details | Conservative fallback unless clearly supported | Pass |

## Security Notes

- Do not commit `.env`.
- Use Streamlit secrets for deployment.
- Keep API keys out of screenshots and documentation.
- Only `.env.example` should be submitted.
- The full source PDF is processed locally; only retrieved snippets are sent to DeepInfra.

## Streamlit Cloud Deployment

1. Push the project without `.env`, `.venv`, `__pycache__`, or `chroma_db`.
2. Create a Streamlit Cloud app with `app.py` as the entrypoint.
3. Add secrets:

```toml
DEEPINFRA_API_KEY = "your_key_here"
DEEPINFRA_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
```

4. Test the evaluation questions and verify sources.

## Submission Checklist

- `app.py`
- `rag_pipeline.py`
- `llm_client.py`
- `answer_guardrails.py`
- `config.py`
- `evaluation.py`
- `requirements.txt`
- `.env.example`
- `README.md`
- `technical_summary.md`
- `test_cases.md`
- `PROJECT_REPORT.md`

Do not submit `.env`, `.venv`, `chroma_db`, or `__pycache__`.
