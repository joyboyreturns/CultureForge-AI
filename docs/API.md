# API

FastAPI serves interactive documentation at `/docs` and the schema at
`/openapi.json`. Every route that takes a body takes a typed one: a body of
the wrong shape is a `422`, with a readable `detail`.

## Error envelope

Every failure has the same shape, so a caller can branch on the code rather
than on the wording:

```json
{"detail": "A sentence for a person.",
 "error": {"code": "RATE_LIMITED", "message": "…", "retryable": true, "details": {"resetsInSeconds": 60}},
 "requestId": "…"}
```

| Code | Status | Meaning |
| --- | --- | --- |
| `INVALID_REQUEST`, `INVALID_UPSTREAM_REQUEST`, `NEEDS_INPUT`, `NO_EVIDENCE`, `UNSUPPORTED_CATEGORY` | 422 | The request, or what Qloo made of it, cannot be answered as asked |
| `NO_CACHED_EVIDENCE` | 409 | A rebuild needs evidence that is not held |
| `RATE_LIMITED`, `ALLOWANCE_EXHAUSTED` | 429 | Qloo rate-limited the key (live calls then pause for a cool-down), or a research run used its allowance |
| `QUOTA_EXHAUSTED`, `LIVE_DISABLED`, `BUDGET_UNAVAILABLE`, `PROVIDER_UNAVAILABLE`, `MODEL_UNAVAILABLE` | 503 | A local budget is used up, the kill switch is on, the ledger is unreadable, Qloo cannot be reached, or no model is configured |
| `UPSTREAM_TIMEOUT`, `RUN_TIMEOUT` | 504 | Qloo or a research run took too long. Nothing is retried blindly. |
| `INTERNAL_ERROR` | 500 | Something unexpected failed on the server. Nothing was changed; quote the `requestId` (the traceback is in the server log) |
| `UPSTREAM_UNAUTHENTICATED`, `UPSTREAM_MALFORMED`, `UPSTREAM_REJECTED` | 502 | Qloo refused the key, answered unreadably, or rejected the request |

## Routes

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/health` | Provider readiness, run profile, budgets (or `unlimited`), cache size. No upstream call. |
| `GET` | `/api/examples` | The prepared briefs and whether each is fully held. No upstream call. |
| `POST` | `/api/projects/generate` | Answer a brief: seeds, places, bridge domains, directions. |
| `POST` | `/api/research/runs` | Start an observable research run (returns 202 and a `runId`). |
| `GET` | `/api/research/runs/{run_id}` | A run's steps, result, clarification or error code. |
| `GET` | `/api/research/runs` | Recent runs. |
| `POST` | `/api/taste/resolve` | Resolve an audience into candidate Qloo tags to confirm. |
| `POST` | `/api/projects/challenge` | The evidence test (policy anchor-fit-5). Optional `anchorEntityId` and `demographic`. |
| `POST` | `/api/profile/propose` | The demographic profile the test would use, before it runs. |
| `POST` | `/api/projects/challenge-probe` | Exclude one cited place and retrieve bounded replacements. |
| `POST` | `/api/projects/recompose` | Rebuild the directions without a place or tag. No new Qloo call. |
| `POST` | `/api/projects/compare` | Re-research the brief for another audience. |
| `POST` | `/api/projects/compare/audiences` | Qloo's comparison of two groups of entities. |
| `POST` | `/api/projects/rank` | Rank entities by affinity for a signal set. |
| `POST` | `/api/projects/investigate` | Investigate one direction through chosen facets. |
| `GET` | `/api/facets` | The facets an investigation can open. |
| `POST` | `/api/projects/analyze` | Model analysis of the directions on screen, citations checked. |
| `POST` | `/api/chat` | *Ask the evidence*: cited answers or a refusal. |
| `POST` | `/api/evidence/presentation` | Let the model choose which of Qloo's own sentences to lead with. |
| `POST` | `/api/report/pdf` | The exploration as a PDF. No upstream call. |
| `GET` | `/api/qloo/workflows` | The nine workflows and how each is called. |
| `POST` | `/api/qloo/describe` · `/entity-tags` · `/where-popular` · `/audience-demographics` · `/trends` | One Qloo workflow each, through the cache. |
| `POST` | `/api/explorations/share` | Freeze an exploration; `GET /api/snapshots/{id}` reopens it (`/studio/?snapshot=<id>`). |
| `GET` | `/api/explorations` · `/{id}` · `/{id}/export` | Saved explorations, and JSON or Markdown export. |
| `POST`/`GET`/`DELETE` | `/api/workspaces…` | Workspaces and issued keys. Needs `CULTUREFORGE_OPERATOR_TOKEN`, or a request from the machine itself. |
| `GET` | `/api/usage` | Request and upstream-call metering. |

`/health` is an alias of `/api/health` for container health checks.

## Examples

```bash
curl -s localhost:8000/api/health
curl -s localhost:8000/api/examples
curl -s -X POST localhost:8000/api/projects/generate -H 'Content-Type: application/json' \
  -d '{"businessType":"Food & beverage","audience":"Design-conscious Gen Z & young professionals",
       "location":"Brooklyn, New York","budget":"$25k – $50k","objectives":[]}'
```

`businessType` is one of `Food & beverage`, `Retail`, `Hospitality`,
`Wellness` and `Entertainment`.


## Business intent and the states around it

`GenerateResponse.intent` (optional) reads the idea: `components` (phrase, category, search strings tried
in order, specialisation `modifiers`), `hybrid`, `ambiguous`, `substitutions` (every simplification, as a
sentence), and `evidence`, one entry per business. Each entry's `state` is one of:

| state | meaning |
|---|---|
| `exact` / `near` | a returned Qloo category tag matched the words (name match; Qloo exposes no hierarchy) |
| `broader` | no tag matched the specific words; a broader search string was used (CultureForge's broadening) |
| `tag_no_places` | the tag exists; Qloo returned no places for it in this city |
| `unresolved` | no returned tag matched any search string tried |
| `not_retrieved` | not held, and this answer may not spend a request |
| `provider_error` | Qloo could not answer (carries `code`); not a statement about coverage |

`UNSUPPORTED_CATEGORY` (422) means find_tags answered and no returned tag matched; it is never produced by a
rate limit, timeout, credential or malformed-response failure, which keep their own codes. A research run that
stops to ask returns `clarification.code` (`UNSUPPORTED_CATEGORY`, `AMBIGUOUS_IDEA`, `CATEGORY_NO_PLACES`) and
`clarification.actions` (`{kind: 'idea', label, value}`) built only from words the founder wrote.
