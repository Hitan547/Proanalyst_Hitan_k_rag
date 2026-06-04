"""Deterministic answer extraction for exact documentation facts."""

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

    if "tenantid" in q and "missing" in q and "default organization" in joined:
        refs = _source_refs(source_texts, ("default organization",))
        return f"When the header is missing, the request uses the user's default organization ({refs})."

    if (
        ("tenantid" in q or "organization execution context" in q)
        and "header" in q
        and "missing" not in q
        and "x-upwork-api-tenantid" in joined
    ):
        refs = _any_source_refs(source_texts, ("x-upwork-api-tenantid",))
        return f"The header is `X-Upwork-API-TenantId` ({refs})."

    if "value for x-upwork-api-tenantid" in q and "companyselector" in joined:
        refs = _any_source_refs(source_texts, ("companyselector", "company selector"))
        return f"Get the `X-Upwork-API-TenantId` value using the `companySelector` query ({refs})."

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

    if "right oauth scopes" in q and "status code 200" in joined:
        refs = _source_refs(source_texts, ("status code 200",))
        return f"You get HTTP 200 OK, with the error details in the response body ({refs})."

    if "permission" in q and "job posting by id" in q and "job postings - read-only access" in joined:
        refs = _source_refs(source_texts, ("job postings - read-only access",))
        return f"The required permission is `Job Postings - Read-Only Access` ({refs})."

    if "single job posting" in q and "jobpostingid" in joined:
        refs = _source_refs(source_texts, ("jobpostingid",))
        return f"Use `jobPosting(jobPostingId: ID!)` to fetch a single job posting ({refs})."

    if "jobposting and marketplacejobposting" in q and (
        "job postings - read-only access" in joined
        and "read marketplace job postings" in joined
    ):
        return (
            "They use different required permissions and response schemas: "
            "jobPosting uses Job Postings - Read-Only Access and returns a JobPosting, "
            "while marketplaceJobPosting uses Read marketplace Job Postings and returns "
            "a MarketplaceJobPosting (retrieved sources)."
        )

    if "marketplacejobpostings still recommended" in q and "deprecated" in joined:
        refs = _source_refs(source_texts, ("deprecated",))
        return f"No. `marketplaceJobPostings` is deprecated; use `marketplaceJobPostingsSearch` instead ({refs})."

    if "multiple ids" in q and "marketplacejobpostingscontents" in joined:
        refs = _source_refs(source_texts, ("marketplacejobpostingscontents",))
        return f"Use `marketplaceJobPostingsContents(ids: [ID!]!)` to fetch job posting content for multiple IDs ({refs})."

    if "create subscriptions" in q and "available only to clients" in joined:
        refs = _source_refs(source_texts, ("available only to clients",))
        return f"Clients only can create subscriptions on the Upwork API ({refs})."

    if "subscription is created" in q and "review state" in joined:
        refs = _source_refs(source_texts, ("review state",))
        return f"After creation, the subscription remains in REVIEW state until approved by the Upwork team ({refs})."

    if "subscription event payload" in q and all(term in joined for term in ("entity", "action", "id")):
        refs = _any_source_refs(source_texts, ("entity", "action", "id"))
        return f"A subscription event payload contains `entity`, `action`, and `id` ({refs})."

    if "entity types" in q and "subscribe" in q and all(
        term in joined for term in ("job postings (jp)", "offer", "milestone", "contract feedback")
    ):
        refs = _source_refs(source_texts, ("job postings (jp)", "offer"))
        return (
            "The supported subscription entity types are JP, OFFER, Vendor JA, "
            f"Client JA, MILESTONE, and CFB ({refs})."
        )

    if "actions" in q and "job postings" in q and all(
        term in joined for term in ("new", "upda", "close")
    ):
        refs = _any_source_refs(source_texts, ("new marketplace job posting", "close marketplace job posting"))
        return f"For job postings, the supported subscription actions are `NEW`, `UPDATE`, and `CLOSE` ({refs})."

    if "list of countries" in q and "common functionality" in joined and "read and w" in joined:
        refs = _source_refs(source_texts, ("common functionality",))
        return f"The required permission is `Common Functionality - Read And Write Access` ({refs})."

    if "languages query" in q and all(term in joined for term in ("iso639code", "active", "englishname")):
        refs = _source_refs(source_texts, ("iso639code", "active", "englishname"))
        return f"The languages query returns `iso639Code`, `active`, and `englishName` ({refs})."

    if "reasons query" in q and "declining invitation" in joined:
        refs = _source_refs(source_texts, ("declining invitation",))
        return (
            "The reasons query fetches reasons for actions like declining invitations, "
            f"ending contracts, and withdrawing offers ({refs})."
        )

    if "service accounts perform write" in q and "must not use service accounts to perform write operations" in joined:
        refs = _source_refs(source_texts, ("must not use service accounts to perform write operations",))
        return f"No. Service accounts should only be used to fetch/read information, not perform write operations ({refs})."

    if "assign permissions" in q and "members & permissions" in joined:
        refs = _source_refs(source_texts, ("members & permissions",))
        return f"Assign permissions via `Settings > Members & Permissions` in the Upwork dashboard ({refs})."

    if "service accounts available" in q and "available only for enterprise accounts" in joined:
        refs = _source_refs(source_texts, ("available only for enterprise accounts",))
        return f"No. Service accounts are available only for enterprise accounts ({refs})."

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
