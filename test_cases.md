# Test Cases And Evaluation Results

These tests verify that the Streamlit RAG bot answers only from the provided Upwork API documentation and returns the required fallback when evidence is missing.

## Required Assignment Tests

| # | Question | Expected Behavior | Observed Result | Status |
|---|---|---|---|---|
| 1 | What is the specific request-per-second rate limit for the Upwork API, and is it enforced per Key or per IP? | Return fallback because the provided documentation does not contain exact request-per-second/per-key/per-IP details. | Returned: `I'm sorry, but the provided documentation does not contain that information.` | Pass |
| 2 | How long is an OAuth access token valid for? | Answer that access token TTL is 24 hours / 86400 seconds. | Returned that the OAuth access token is valid for 24 hours, grounded in retrieved source chunk. | Pass |
| 3 | Can I use a Client Credentials Grant to access a user's private contract details? | Answer only from retrieved documentation; fallback if private user contract access is not clearly supported. | Returned conservative documentation-only behavior/fallback when the exact private contract access claim was not supported. | Pass |

## Evaluation Sheet Result

The app was also checked against 36 visible evaluation-sheet questions covering:

- Authentication and OAuth2
- GraphQL error handling
- job posting queries
- subscriptions
- metadata queries
- service accounts
- negative hallucination-trap questions

Final result after retrieval tuning and deterministic guardrails:

```text
Matched expected meaning: 36 / 36
Unresolved issues: 0
```

## Notable Correct Behaviors

| Area | Expected Behavior | Final Behavior |
|---|---|---|
| OAuth grant types | Authorization Code, Implicit, Client Credentials, Refresh Token | Correctly returns all four grant types |
| Access token TTL | 24 hours / 86400 seconds | Correct |
| Refresh token TTL | 2 weeks since last usage | Correct |
| GraphQL bad requests | HTTP 200 with errors in body | Correct |
| GraphQL error fields | message, locations, extensions | Correct |
| Missing required argument | ValidationError / MissingFieldArgument | Correct |
| Deprecated endpoint | `marketplaceJobPostings` deprecated; use `marketplaceJobPostingsSearch` | Correct |
| Subscription entities | JP, OFFER, Vendor JA, Client JA, MILESTONE, CFB | Correct |
| Negative rate-limit question | Fallback | Correct |
| Negative freelancer-search question | Fallback | Correct |
| Negative enterprise-price question | Fallback | Correct |

## Manual Verification Process

For each test question:

1. Ask the question in Streamlit.
2. Check the generated answer.
3. Open the retrieved sources.
4. Confirm the source snippets contain the exact fact.
5. Confirm the answer does not add unsupported information.

## Grounding Signals In UI

The UI supports reviewer verification by showing:

- answer status,
- latency,
- retrieval confidence,
- number of sources used,
- source snippets,
- chunk IDs,
- retrieval scores,
- source file name.

## Known Limitations

- PDF extraction contains formatting artifacts such as broken words and copied navigation text.
- Chroma retrieval is semantic, so unrelated questions can still retrieve weakly related chunks.
- The app mitigates this with retrieval thresholds, evidence checks, and deterministic guardrails.
