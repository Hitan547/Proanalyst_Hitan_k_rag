"""Application configuration for the Upwork API RAG bot."""

from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


def get_secret(name: str, default: str = "") -> str:
    """Read config from environment variables first, then Streamlit secrets."""
    env_value = os.getenv(name)
    if env_value:
        return env_value

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default

BASE_DIR = Path(__file__).resolve().parent

PDF_PATH = BASE_DIR / "data" / "upwork_api_docs.pdf"
VECTOR_DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "upwork_api_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEEPINFRA_API_KEY = get_secret("DEEPINFRA_API_KEY", "")
DEEPINFRA_API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
DEEPINFRA_MODEL = get_secret(
    "DEEPINFRA_MODEL",
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
)
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 700

FALLBACK_MESSAGE = (
    "I'm sorry, but the provided documentation does not contain that information."
)

# Chroma relevance scores are normalized in rag_pipeline.py so higher is better.
RETRIEVAL_THRESHOLD = 0.35
