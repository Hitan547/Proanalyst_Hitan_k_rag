"""Evaluation questions for quick Streamlit testing."""

EVALUATION_QUESTIONS = [
    "What is the specific request-per-second rate limit for the Upwork API, and is it enforced per Key or per IP?",
    "How long is an OAuth access token valid for?",
    "Can I use a Client Credentials Grant to access a user's private contract details?",
]

SHEET_EVALUATION_CASES = [
    {
        "question": "What OAuth 2.0 grant types does Upwork support?",
        "expected": "Authorization Code, Implicit, Client Credentials, Refresh Token",
    },
    {
        "question": "How long is an OAuth access token valid for?",
        "expected": "24 hours (86400 seconds)",
    },
    {
        "question": "How long is an OAuth refresh token valid for?",
        "expected": "2 weeks since last usage",
    },
    {
        "question": "Which OAuth grant is available only for enterprise accounts?",
        "expected": "Client Credentials Grant",
    },
    {
        "question": "What authorization endpoint is used to obtain an authorization code?",
        "expected": "GET https://www.upwork.com/ab/account-security/oauth2/authorize",
    },
    {
        "question": "What token endpoint is used to obtain an access token?",
        "expected": "POST https://www.upwork.com/api/v3/oauth2/token",
    },
    {
        "question": "What header sets the Upwork organization execution context?",
        "expected": "X-Upwork-API-TenantId",
    },
    {
        "question": "What happens when the X-Upwork-API-TenantId header is missing?",
        "expected": "Uses the user's default organization",
    },
    {
        "question": "How do I get the value for X-Upwork-API-TenantId?",
        "expected": "Via companySelector query",
    },
    {
        "question": "Which parameters are required for Authorization Code token request?",
        "expected": "grant_type, client_id, client_secret, code, redirect_uri",
    },
    {
        "question": "Does Upwork's GraphQL API return HTTP 400 for bad requests?",
        "expected": "No, it always returns HTTP 200; errors are in the response body",
    },
    {
        "question": "What are the three components of a GraphQL error response in Upwork?",
        "expected": "message, locations, extensions",
    },
    {
        "question": "When does Upwork return a 5XX HTTP status code?",
        "expected": "When the failure occurs at the GraphQL layer itself",
    },
    {
        "question": "What error classification appears when you query a field without required arguments?",
        "expected": "ValidationError (MissingFieldArgument)",
    },
    {
        "question": "If I don't have the right OAuth scopes, what HTTP status code will I get?",
        "expected": "200 OK, with the error in the response body",
    },
    {
        "question": "What permission is required to query a job posting by ID?",
        "expected": "Job Postings - Read-Only Access",
    },
    {
        "question": "What GraphQL query do I use to fetch a single job posting?",
        "expected": "jobPosting(jobPostingId: ID!)",
    },
    {
        "question": "What is the difference between jobPosting and marketplaceJobPosting?",
        "expected": "Different required permissions and response schemas",
    },
    {
        "question": "Is marketplaceJobPostings still recommended to use?",
        "expected": "No, it is deprecated; use marketplaceJobPostingsSearch instead",
    },
    {
        "question": "How do I fetch job posting content for multiple IDs at once?",
        "expected": "marketplaceJobPostingsContents(ids: [ID!]!)",
    },
    {
        "question": "Who can create subscriptions on the Upwork API?",
        "expected": "Clients only (not freelancers)",
    },
    {
        "question": "What happens after a subscription is created?",
        "expected": "It goes into REVIEW state until approved by the Upwork team",
    },
    {
        "question": "What three fields does a subscription event payload contain?",
        "expected": "entity, action, id",
    },
    {
        "question": "What entity types can I subscribe to?",
        "expected": "JP, OFFER, Vendor JA, Client JA, MILESTONE, CFB",
    },
    {
        "question": "What actions can I subscribe to for job postings?",
        "expected": "NEW, UPDATE, CLOSE",
    },
    {
        "question": "What permissions do I need to query the list of countries?",
        "expected": "Common Functionality - Read And Write Access",
    },
    {
        "question": "What fields are returned in the languages query?",
        "expected": "iso639Code, active, englishName",
    },
    {
        "question": "What is the reasons query used for?",
        "expected": "Fetching reasons for actions like declining invitations, ending contracts, withdrawing offers",
    },
    {
        "question": "Can service accounts perform write operations?",
        "expected": "No, they should only be used to fetch/read information",
    },
    {
        "question": "How do you assign permissions to a service account?",
        "expected": "Via Settings > Members & Permissions in the Upwork dashboard",
    },
    {
        "question": "Are service accounts available to all Upwork users?",
        "expected": "No, enterprise accounts only",
    },
    {
        "question": "What is the rate limit for Upwork API calls?",
        "expected": "Not covered in the documentation",
    },
    {
        "question": "How do I search for freelancers via the API?",
        "expected": "Not covered in the documentation",
    },
    {
        "question": "What is the price of an Upwork enterprise plan?",
        "expected": "Not covered in the documentation",
    },
    {
        "question": "Can I use the Implicit Grant to get a refresh token?",
        "expected": "No, Implicit Grant only returns an access token, no refresh token",
    },
    {
        "question": "What scopes are available for the Upwork API?",
        "expected": "Doc references scopes but doesn't list them",
    },
]
