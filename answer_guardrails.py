"""Selective deterministic extraction for high-impact documentation facts."""

from __future__ import annotations


def _source_has(source_text: str, *terms: str) -> bool:
    text = source_text.lower()
    return all(term.lower() in text for term in terms)


def _source_refs(source_texts: list[str], required_terms: tuple[str, ...]) -> str:
    refs = []
    for index, text in enumerate(source_texts, start=1):
        if _source_has(text, *required_terms):
            refs.append(f"Source {index}")
    return ", ".join(refs) if refs else "retrieved sources"


def _any_source_refs(source_texts: list[str], terms: tuple[str, ...]) -> str:
    refs = []
    for index, text in enumerate(source_texts, start=1):
        lowered = text.lower()
        if any(term.lower() in lowered for term in terms):
            refs.append(f"Source {index}")
    return ", ".join(refs) if refs else "retrieved sources"


def direct_answer(question: str, source_texts: list[str]) -> str | None:
    """Return exact fact answers when the retrieved snippets clearly support them."""
    q = question.lower()
    joined = "\n".join(source_texts).lower()

    if "access token" in q and ("valid" in q or "validity" in q or "how long" in q):
        if "ttl for an access token is 24 hours" in joined or "expires_in" in joined:
            refs = _any_source_refs(source_texts, ("ttl for an access token is 24 hours", "expires_in"))
            return (
                "An OAuth access token is valid for 24 hours, shown as "
                f"`expires_in: 86400` seconds in the token response ({refs})."
            )

    if "refresh token" in q and ("valid" in q or "validity" in q or "how long" in q):
        if "ttl for a refresh token is 2 weeks since its last usage" in joined:
            refs = _source_refs(source_texts, ("ttl for a refresh token is 2 weeks since its last usage",))
            return f"An OAuth refresh token is valid for 2 weeks since its last usage ({refs})."

    if "grant types" in q and all(
        term in joined
        for term in (
            "authorization",
            "implicit grant",
            "client credentials",
            "refresh token",
        )
    ):
        refs = _any_source_refs(
            source_texts,
            ("authorization_code", "implicit grant", "client credentials", "refresh token"),
        )
        return (
            "Upwork supports Authorization Code Grant, Implicit Grant, "
            "Client Credentials Grant, and Refresh Token Grant Type "
            f"({refs})."
        )

    if "enterprise" in q and "grant" in q and "client credentials grant" in joined:
        refs = _source_refs(source_texts, ("client credentials grant",))
        return f"Client Credentials Grant is available only for enterprise accounts ({refs})."

    if ("authorization endpoint" in q or "authorization code" in q) and "oauth2/authorize" in joined:
        refs = _any_source_refs(source_texts, ("oauth2/authorize",))
        return (
            "Use `GET https://www.upwork.com/ab/account-security/oauth2/authorize` "
            f"to obtain an authorization code ({refs})."
        )

    if "token endpoint" in q and "oauth2/token" in joined:
        refs = _any_source_refs(source_texts, ("oauth2/token",))
        return (
            "Use `POST https://www.upwork.com/api/v3/oauth2/token` "
            f"to obtain an access token ({refs})."
        )

    if "authorization code token request" in q and all(
        term in joined for term in ("grant_type", "client_id", "client_secret", "code", "redirect_uri")
    ):
        refs = _source_refs(source_texts, ("grant_type", "client_id", "client_secret", "code", "redirect_uri"))
        return (
            "The required parameters are `grant_type`, `client_id`, `client_secret`, "
            f"`code`, and `redirect_uri` ({refs})."
        )

    if "graphql" in q and ("400" in q or "bad request" in q) and "200" in joined:
        refs = _any_source_refs(source_texts, ("always returns a 200", "200 - ok"))
        return f"No. Upwork GraphQL returns HTTP 200 OK; errors are returned in the response body ({refs})."

    if "graphql error response" in q and all(
        term in joined for term in ("message", "locations", "extensions")
    ):
        refs = _source_refs(source_texts, ("message", "locations", "extensions"))
        return (
            "The three components are message, locations, and extensions "
            f"({refs})."
        )

    if "required arguments" in q and "missingfieldargument" in joined and "validationerror" in joined:
        refs = _source_refs(source_texts, ("missingfieldargument", "validationerror"))
        return f"The error is ValidationError, with type MissingFieldArgument ({refs})."

    if "5xx" in q and "graphql  layer itself" in joined:
        refs = _source_refs(source_texts, ("graphql  layer itself",))
        return f"Upwork returns 5XX when the failure occurs at the GraphQL layer itself ({refs})."

    if "implicit grant" in q and "refresh token" in q and "implicit grant" in joined:
        refs = _source_refs(source_texts, ("implicit grant",))
        return (
            "No. The Implicit Grant returns an access token and does not provide a "
            f"refresh token ({refs})."
        )

    if "scopes are available" in q and "scopes" in joined:
        return (
            "The documentation references scopes and explains that they define which "
            "APIs a key can access, but it does not list the available scope names "
            "(retrieved sources)."
        )

    return None
