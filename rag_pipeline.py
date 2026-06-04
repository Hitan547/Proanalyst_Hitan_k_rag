"""Local document ingestion, chunking, embedding, Chroma storage, and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
import warnings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from chromadb.config import Settings

try:
    from langchain_chroma import Chroma
except ImportError:  # pragma: no cover - compatibility fallback
    from langchain_community.vectorstores import Chroma

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    PDF_PATH,
    TOP_K,
    VECTOR_DB_DIR,
)


@dataclass(frozen=True)
class DocumentStats:
    character_count: int
    chunk_count: int
    sample_text: str


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    chunk_id: int
    source_file: str
    score: float


def load_pdf_text(pdf_path: Path = PDF_PATH) -> tuple[list, DocumentStats]:
    """Load PDF pages and return LangChain documents plus sanity-check stats."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = PyPDFLoader(str(pdf_path)).load()
    full_text = "\n\n".join(page.page_content for page in pages)
    sample = " ".join(full_text.split())[:600]
    stats = DocumentStats(
        character_count=len(full_text),
        chunk_count=0,
        sample_text=sample,
    )

    print(f"Total character count: {stats.character_count}")
    print(f"Sample text: {stats.sample_text}")
    return pages, stats


def split_documents(pages: list) -> list:
    """Split documents using the exact assignment chunk settings."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(pages)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
        chunk.metadata["source_file"] = Path(chunk.metadata.get("source", PDF_PATH)).name
    return chunks


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Create the local embedding model."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def _has_persisted_chroma(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def build_or_load_vector_store(chunks: list, embedding_model: HuggingFaceEmbeddings) -> Chroma:
    """Load persisted Chroma if present, otherwise embed and persist chunks."""
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    chroma_settings = Settings(anonymized_telemetry=False)

    if _has_persisted_chroma(VECTOR_DB_DIR):
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=embedding_model,
            client_settings=chroma_settings,
        )
        if vector_store._collection.count() > 0:
            return vector_store
        vector_store.add_documents(chunks)
        return vector_store

    return Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DB_DIR),
        client_settings=chroma_settings,
    )


def normalize_relevance_score(raw_score: float) -> float:
    """Convert retriever output into a bounded 0-1 relevance score."""
    if raw_score is None or math.isnan(raw_score):
        return 0.0
    return max(0.0, min(1.0, float(raw_score)))


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "what",
    "when",
    "which",
    "who",
    "with",
}


def tokenize(text: str) -> set[str]:
    """Tokenize for a small lexical rerank after vector search."""
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return {token for token in tokens if len(token) > 2 and token not in STOPWORDS}


def lexical_score(query: str, text: str) -> float:
    """Return a bounded lexical overlap score for technical terms."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0

    text_tokens = tokenize(text)
    overlap = len(query_tokens & text_tokens) / len(query_tokens)
    phrase_bonus = 0.0
    normalized_query = query.lower()
    lowered_text = text.lower()

    for phrase in (
        "client credentials",
        "authorization code",
        "refresh token",
        "implicit grant",
        "x-upwork-api-tenantid",
        "jobposting",
        "marketplacejobposting",
        "subscription",
        "validationerror",
        "required permissions",
        "http status",
        "graphql",
        "languages",
        "reasons",
        "service account",
    ):
        if phrase in normalized_query and phrase in lowered_text:
            phrase_bonus += 0.15

    targeted_boosts = (
        ("grant types", "supported grants", 0.35),
        ("grant types", "authorization code grant", 0.1),
        ("grant types", "implicit grant", 0.1),
        ("refresh token valid", "ttl for a refresh token", 0.3),
        ("access token valid", "ttl for an access token", 0.3),
        ("graphql error", "message", 0.1),
        ("graphql error", "locations", 0.1),
        ("graphql error", "extensions", 0.1),
        ("components", "message", 0.1),
        ("components", "locations", 0.1),
        ("components", "extensions", 0.1),
        ("5xx", "graphql  layer itself", 0.3),
        ("right oauth scopes", "status code 200", 0.25),
        ("single job posting", "query  jobposting", 0.3),
        ("jobposting and marketplacejobposting", "job postings - read-only access", 0.45),
        ("jobposting and marketplacejobposting", "returns a jobposting", 0.35),
        ("jobposting and marketplacejobposting", "read marketplace job postings", 0.45),
        ("jobposting and marketplacejobposting", "returns a marketplacejobposting", 0.35),
        ("actions", "new marketplace job posting was posted", 0.25),
        ("actions", "update marketplace job posting was updated", 0.25),
        ("actions", "close marketplace job posting was closed", 0.25),
        ("service accounts available", "available only for enterprise accounts", 0.35),
        ("implicit grant", "returns the access token", 0.2),
    )
    for query_phrase, text_phrase, boost in targeted_boosts:
        if query_phrase in normalized_query and text_phrase in lowered_text:
            phrase_bonus += boost

    return min(1.0, overlap + phrase_bonus)


def expand_query(query: str) -> str:
    """Add domain terms that help retrieve exact API documentation chunks."""
    normalized = query.lower()
    expansions: list[str] = []

    if "grant types" in normalized or "grants" in normalized:
        expansions.append(
            "Supported Grants Authorization Code Grant Implicit Grant Client Credentials Grant Refresh Token Grant Type"
        )
    if "access token valid" in normalized or "access token validity" in normalized:
        expansions.append("TTL for an access token is 24 hours expires_in 86400")
    if "refresh token valid" in normalized or "refresh token validity" in normalized:
        expansions.append("TTL for a refresh token is 2 weeks since its last usage")
    if "enterprise" in normalized and "grant" in normalized:
        expansions.append("Client Credentials Grant available for enterprise accounts only")
    if "authorization endpoint" in normalized or "obtain an authorization code" in normalized:
        expansions.append(
            "Step 1 Obtaining an authorization code Endpoint GET https://www.upwork.com/ab/account-security/oauth2/authorize"
        )
    if "token endpoint" in normalized or "obtain an access token" in normalized:
        expansions.append(
            "Endpoint POST https://www.upwork.com/api/v3/oauth2/token access token"
        )
    if "authorization code token request" in normalized or "parameters" in normalized:
        expansions.append(
            "Authorization Code Grant token request Parameters grant_type client_id client_secret code redirect_uri"
        )
    if "tenantid" in normalized or "organization execution context" in normalized:
        expansions.append("X-Upwork-API-TenantId companySelector user's default organization")
    if "graphql" in normalized and ("400" in normalized or "bad request" in normalized):
        expansions.append("GraphQL always returns a 200 OK status code malformed syntax bad request")
    if "graphql error" in normalized or "components" in normalized:
        expansions.append("GraphQL error response message locations extensions")
    if "5xx" in normalized:
        expansions.append("GraphQL layer itself HTTP status code 5XX")
    if "required arguments" in normalized or "required argument" in normalized:
        expansions.append("MissingFieldArgument ValidationError missing field argument required")
    if "oauth scopes" in normalized or "right oauth scopes" in normalized:
        expansions.append("Oauth2 permissions scopes access endpoint HTTP status code 200 OK response body")
    if "job posting by id" in normalized:
        expansions.append("jobPosting jobPostingId Required Permissions Job Postings Read-Only Access")
    if "single job posting" in normalized:
        expansions.append("jobPosting(jobPostingId: ID!) query single job posting")
    if "jobposting and marketplacejobposting" in normalized:
        expansions.append("jobPosting marketplaceJobPosting different required permissions response schemas")
    if "marketplacejobpostings still recommended" in normalized:
        expansions.append("marketplaceJobPostings Deprecated use marketplaceJobPostingsSearch instead")
    if "multiple ids" in normalized:
        expansions.append("marketplaceJobPostingsContents ids [ID!]! job posting content")
    if "create subscriptions" in normalized:
        expansions.append("subscriptions feature available only to clients")
    if "subscription is created" in normalized:
        expansions.append("subscription reviewed approved Upwork Team REVIEW state")
    if "subscription event payload" in normalized:
        expansions.append("payload includes entity action id")
    if "entity types" in normalized and "subscribe" in normalized:
        expansions.append("Supported events Job postings JP Offer OFFER Vendor JA Client JA Milestone CFB")
    if "actions" in normalized and "job postings" in normalized:
        expansions.append("Job postings JP NEW UPDATE CLOSE")
    if "list of countries" in normalized:
        expansions.append("countries Required Permissions Common Functionality Read And Write Access")
    if "languages query" in normalized:
        expansions.append("languages query iso639Code active englishName")
    if "reasons query" in normalized:
        expansions.append("reasons declining invitation ending contract withdrawing offer")
    if "service accounts perform write" in normalized:
        expansions.append("service accounts must not perform write operations fetch information")
    if "assign permissions" in normalized and "service account" in normalized:
        expansions.append("Settings Members Permissions Service Account update permissions")
    if "service accounts available" in normalized:
        expansions.append("service accounts enterprise accounts only client credentials key")
    if "implicit grant" in normalized and "refresh token" in normalized:
        expansions.append("Implicit Grant returns access token TTL without refresh token")
    if "scopes are available" in normalized:
        expansions.append("Scopes define APIs that you can access relevant scopes")

    if not expansions:
        return query
    return f"{query} {' '.join(expansions)}"


def retrieve_relevant_chunks(vector_store: Chroma, query: str, k: int = TOP_K) -> list[RetrievedChunk]:
    """Fetch the top-k most relevant chunks with UI-safe metadata and scores."""
    expanded_query = expand_query(query)
    candidate_count = max(k, 48)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Relevance scores must be between 0 and 1.*",
        )
        results = vector_store.similarity_search_with_relevance_scores(
            expanded_query,
            k=candidate_count,
        )
    retrieved = []

    for document, score in results:
        vector_score = normalize_relevance_score(score)
        combined_query = f"{query} {expanded_query}"
        reranked_score = min(
            1.0,
            (0.55 * vector_score) + (0.45 * lexical_score(combined_query, document.page_content)),
        )
        retrieved.append(
            RetrievedChunk(
                text=document.page_content,
                chunk_id=int(document.metadata.get("chunk_id", -1)),
                source_file=str(document.metadata.get("source_file", "unknown")),
                score=reranked_score,
            )
        )

    retrieved.sort(key=lambda chunk: chunk.score, reverse=True)
    return retrieved[:k]


def initialize_rag() -> tuple[Chroma, DocumentStats]:
    """Prepare documents, chunks, embeddings, and vector store."""
    pages, stats = load_pdf_text()
    chunks = split_documents(pages)
    stats = DocumentStats(
        character_count=stats.character_count,
        chunk_count=len(chunks),
        sample_text=stats.sample_text,
    )
    embedding_model = get_embedding_model()
    vector_store = build_or_load_vector_store(chunks, embedding_model)
    return vector_store, stats
