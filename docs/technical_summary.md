# Technical Summary

I built a Streamlit-based RAG assistant that answers Upwork API questions using only the provided documentation. The system loads the local PDF, verifies extraction with character count and sample text, chunks the content into 500-character chunks with 50-character overlap, embeds the chunks locally using `sentence-transformers/all-MiniLM-L6-v2`, stores them in persistent ChromaDB, retrieves the top 3 relevant chunks, and sends only those snippets to DeepInfra Meta-Llama for answer generation.

The 500-character chunk size and 50-character overlap were used exactly as required. The overlap is important for technical documentation because OAuth flows, endpoint URLs, curl commands, GraphQL schemas, permissions, and request parameters can span chunk boundaries. Without overlap, a retrieved chunk may contain only part of the fact needed to answer accurately.

I selected ChromaDB because it persists embeddings locally. After the first indexing run, the app can restart without recomputing embeddings, improving startup time and developer experience. I used MiniLM because it is lightweight, local, cost-free for embeddings, and strong enough for semantic search over API documentation.

During testing, I found that retrieval alone was not always enough for exact API facts. The vector store could retrieve relevant chunks, but the LLM sometimes omitted one list item or returned fallback even when the source contained the answer. I solved this with deterministic answer guardrails for exact source-supported facts, such as OAuth grant types, GraphQL error fields, subscription entities, and Implicit Grant refresh-token behavior. These guardrails only fire when retrieved snippets clearly contain the evidence, so the system remains grounded in the provided documentation.

The app includes hallucination protection through a retrieval threshold, evidence checks, a strict prompt, deterministic fact guardrails, and visible source snippets. The UI shows answer status, latency, retrieval confidence, source count, exact snippets, chunk IDs, and scores, making every answer auditable.

The final system was tested against the required assignment questions and the visible evaluation-sheet questions. After retrieval tuning and guardrails, all 36 evaluation answers matched the expected meaning while remaining grounded in retrieved source snippets.

## Use Of AI Assistance

I used LLM assistance for planning, debugging, documentation structure, and code review. The application itself does not upload the full source documentation to the hosted model. Only the top retrieved snippets are sent to DeepInfra during answer generation.

## Why I Am A Strong Fit For ProAnalyst

- I focus on trustworthy AI behavior: source grounding, fallback handling, and answer traceability.
- I can build practical RAG systems end to end: ingestion, chunking, embeddings, vector search, prompting, UI, and evaluation.
- I pay attention to engineering quality: environment-based secrets, persistent vector storage, clear architecture, test cases, and explainable design decisions.
