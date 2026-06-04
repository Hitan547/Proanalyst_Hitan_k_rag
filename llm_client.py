"""DeepInfra chat-completions client for the RAG answer step."""

from __future__ import annotations

import time
from typing import Iterable

import requests

from config import (
    DEEPINFRA_API_KEY,
    DEEPINFRA_API_URL,
    DEEPINFRA_MODEL,
    FALLBACK_MESSAGE,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)


SYSTEM_PROMPT = f"""You are a Senior Upwork API Consultant.

Answer the user's question using only the provided documentation snippets.

If a snippet directly contains the requested fact, answer it concisely using that snippet.
Use all provided snippets, not only Source 1.
Do not answer with the fallback message after already stating a source-supported answer.

If the answer is not clearly present in the snippets, respond exactly:
"{FALLBACK_MESSAGE}"

Do not use outside knowledge.
Do not guess.
Do not invent policies, limits, API behavior, token validity, rate limits, permissions, or grant behavior.
Cite every relevant source snippet by number when answering. If one source supports part
of the answer and another source supports another part, cite both source numbers.

For GraphQL error questions, distinguish between the error type in the message and the
classification in extensions when both appear in the snippets.

For questions asking what scopes are available, if the snippets reference scopes but do
not list the scope names, say that the documentation references scopes but does not list
the available scopes."""


def build_user_prompt(question: str, source_texts: Iterable[str]) -> str:
    """Build the LLM prompt without exposing chunk IDs or scores."""
    sources = []
    for index, text in enumerate(source_texts, start=1):
        sources.append(f"[Source {index}]\n{text.strip()}")

    return "\n\n".join(sources) + f"\n\nUser question:\n{question.strip()}"


def generate_answer(question: str, source_texts: list[str]) -> tuple[str, float]:
    """Call DeepInfra and return the answer plus API latency in seconds."""
    if not DEEPINFRA_API_KEY:
        raise ValueError("DEEPINFRA_API_KEY is missing. Add it to your .env file.")

    payload = {
        "model": DEEPINFRA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, source_texts)},
        ],
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json",
    }

    start = time.perf_counter()
    response = requests.post(
        DEEPINFRA_API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    latency = time.perf_counter() - start

    if response.status_code == 401:
        raise ValueError(
            "DeepInfra returned 401 Unauthorized. Check that DEEPINFRA_API_KEY is valid "
            "and copied exactly from the provider."
        )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"DeepInfra API request failed: {response.status_code}") from exc

    data = response.json()
    answer = data["choices"][0]["message"]["content"].strip()
    return answer, latency
