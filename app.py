"""Streamlit UI for the Upwork API documentation RAG bot."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Upwork API Support Bot",
    layout="wide",
)

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEEPINFRA_MODEL,
    EMBEDDING_MODEL,
    FALLBACK_MESSAGE,
    RETRIEVAL_THRESHOLD,
    TOP_K,
)
from answer_guardrails import direct_answer
from evaluation import EVALUATION_QUESTIONS
from llm_client import generate_answer
from rag_pipeline import initialize_rag, retrieve_relevant_chunks


EVALUATION_BUTTONS = [
    ("Rate Limit", EVALUATION_QUESTIONS[0]),
    ("OAuth Token TTL", EVALUATION_QUESTIONS[1]),
    ("Client Credentials", EVALUATION_QUESTIONS[2]),
]


@st.cache_resource(show_spinner="Loading documents and vector store...")
def get_rag_resources():
    """Cache the embedding model and Chroma vector store across reruns."""
    return initialize_rag()


def apply_page_styles():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        div[data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }
        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.35);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 8px;
            border-color: rgba(148, 163, 184, 0.38) !important;
            background: rgba(15, 23, 42, 0.34);
            box-shadow: none !important;
        }
        div[data-testid="stTextArea"] textarea:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 1px #38bdf8 !important;
            outline: none !important;
        }
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            border-color: rgba(148, 163, 184, 0.38) !important;
            box-shadow: none !important;
        }
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 1px #38bdf8 !important;
        }
        div.stButton > button {
            border-radius: 8px;
            min-height: 2.75rem;
            font-weight: 600;
        }
        div.stButton > button[kind="primary"] {
            background: #0ea5e9;
            border-color: #0ea5e9;
        }
        .hero {
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
            padding-bottom: 1.15rem;
            margin-bottom: 1.6rem;
        }
        .hero-title {
            font-size: 2.15rem;
            font-weight: 750;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }
        .hero-copy {
            color: #94a3b8;
            font-size: 1rem;
            margin-bottom: 0;
        }
        .status-box {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: rgba(15, 23, 42, 0.32);
            margin: 0.4rem 0 1rem 0;
        }
        .status-label {
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }
        .status-value {
            font-weight: 700;
            font-size: 1rem;
        }
        .ok { color: #22c55e; }
        .warn { color: #f59e0b; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">Upwork API Technical Support Bot</div>
            <p class="hero-copy">
                RAG assistant grounded only in the provided Upwork API documentation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def retrieval_confidence(score: float) -> str:
    """Convert normalized relevance into a review-friendly label."""
    if score >= 0.75:
        return "High"
    if score >= RETRIEVAL_THRESHOLD:
        return "Medium"
    return "Low"


def has_required_evidence(question: str, source_texts: list[str]) -> bool:
    """Catch cases where retrieval is topical but lacks the exact requested fact."""
    normalized_question = question.lower()
    normalized_sources = "\n".join(source_texts).lower()

    if "rate" in normalized_question and "limit" in normalized_question:
        rate_limit_terms = (
            "rate limit",
            "request-per-second",
            "requests per second",
            "per second",
            "per key",
            "per ip",
        )
        return any(term in normalized_sources for term in rate_limit_terms)

    return True


def grounding_status(answer: str, sources) -> tuple[str, str]:
    """Return a UI label and color class for the generated answer."""
    if answer.strip() == FALLBACK_MESSAGE:
        return "Fallback: not found in provided docs", "warn"
    if sources:
        return "Grounding: source-supported", "ok"
    return "Grounding: no source retrieved", "warn"


def answer_question(question: str):
    """Retrieve sources, apply fallback threshold, and call the LLM if useful."""
    vector_store, _ = get_rag_resources()
    sources = retrieve_relevant_chunks(vector_store, question, k=TOP_K)
    best_score = max((source.score for source in sources), default=0.0)
    confidence = retrieval_confidence(best_score)

    if best_score < RETRIEVAL_THRESHOLD:
        return FALLBACK_MESSAGE, 0.0, confidence, sources

    source_texts = [source.text for source in sources]
    if not has_required_evidence(question, source_texts):
        return FALLBACK_MESSAGE, 0.0, confidence, sources

    guarded_answer = direct_answer(question, source_texts)
    if guarded_answer:
        return guarded_answer, 0.0, confidence, sources

    answer, latency = generate_answer(question, source_texts)
    return answer, latency, confidence, sources


def render_sidebar(stats):
    st.sidebar.header("Document Stats")
    st.sidebar.metric("Characters", f"{stats.character_count:,}")
    st.sidebar.metric("Chunks", f"{stats.chunk_count:,}")

    st.sidebar.header("Retrieval Settings")
    st.sidebar.write(f"Chunk Size: {CHUNK_SIZE}")
    st.sidebar.write(f"Overlap: {CHUNK_OVERLAP}")
    st.sidebar.write(f"Top-K: {TOP_K}")
    st.sidebar.write(f"Threshold: {RETRIEVAL_THRESHOLD:.2f}")

    st.sidebar.header("Models")
    st.sidebar.write(f"Embeddings: {EMBEDDING_MODEL.split('/')[-1]}")
    st.sidebar.write(f"LLM: {DEEPINFRA_MODEL.split('/')[-1]}")
    st.sidebar.write("Vector DB: Chroma")

    with st.sidebar.expander("Sanity Check Sample"):
        st.write(stats.sample_text)


def render_sources(sources):
    st.subheader("Sources")
    if not sources:
        st.info("No sources retrieved.")
        return

    for index, source in enumerate(sources, start=1):
        with st.expander(
            f"Source {index} (Chunk {source.chunk_id}) - Score: {source.score:.2f}",
            expanded=index == 1,
        ):
            st.caption(f"Source file: {source.source_file}")
            st.write(source.text)


def render_evaluation_reference():
    with st.expander("Evaluation Reference", expanded=False):
        st.table(
            [
                {
                    "Question": "Rate limit",
                    "Expected Behavior": "Fallback if exact request-per-second/per-key/per-IP detail is absent.",
                    "Status": "Manual check",
                },
                {
                    "Question": "OAuth token validity",
                    "Expected Behavior": "Answer from sources: access token TTL is 24 hours.",
                    "Status": "Manual check",
                },
                {
                    "Question": "Client Credentials",
                    "Expected Behavior": "Answer only from retrieved docs; fallback if private user contract access is unsupported.",
                    "Status": "Manual check",
                },
            ]
        )


def main():
    apply_page_styles()
    render_header()

    try:
        _, stats = get_rag_resources()
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    render_sidebar(stats)
    render_evaluation_reference()

    st.subheader("Quick Evaluation")
    cols = st.columns(len(EVALUATION_BUTTONS))
    for index, (label, question_text) in enumerate(EVALUATION_BUTTONS):
        if cols[index].button(label, use_container_width=True):
            st.session_state["question"] = question_text

    example_questions = [
        "",
        "What OAuth 2.0 grant types does Upwork support?",
        "What endpoint do I call to get an authorization code?",
        "Does Upwork's GraphQL API return HTTP 400 for bad requests?",
        "What permission is required to query a job posting by ID?",
        "Can service accounts perform write operations?",
    ]
    selected_example = st.selectbox(
        "Example questions",
        example_questions,
        format_func=lambda value: "Select an example..." if not value else value,
    )
    if selected_example:
        st.session_state["question"] = selected_example

    question = st.text_area(
        "Question",
        value=st.session_state.get("question", ""),
        height=120,
        placeholder="Ask a question about the Upwork API documentation...",
    )

    ask_clicked = st.button("Ask documentation", type="primary")
    if ask_clicked:
        if not question.strip():
            st.warning("Please enter a question.")
            st.stop()

        with st.spinner("Retrieving sources and generating answer..."):
            try:
                answer, latency, confidence, sources = answer_question(question)
            except Exception as exc:
                st.error(str(exc))
                st.stop()

        label, label_class = grounding_status(answer, sources)
        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-label">Answer Status</div>
                <div class="status-value {label_class}">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_cols = st.columns(3)
        metric_cols[0].metric("Latency", f"{latency:.2f}s")
        metric_cols[1].metric("Retrieval Confidence", confidence)
        metric_cols[2].metric("Sources Used", len(sources))

        st.subheader("Answer")
        st.write(answer)

        render_sources(sources)


if __name__ == "__main__":
    main()
