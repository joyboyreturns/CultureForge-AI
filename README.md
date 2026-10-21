# CultureForge AI

**Turn cultural evidence into business ideas a founder can challenge.**

CultureForge is an agentic concept studio for local founders. It uses Qloo's cultural intelligence to connect an audience and place to real venues, then proposes business directions whose evidence, assumptions, and weak points are visible. A direction can be supported, contested, or left unproven. The product does not pretend cultural affinity is proof of demand.

> **Hackathon submission links:** Live demo: _add the public deployment URL_. Source: [CultureForge AI on GitHub](https://github.com/joyboyreturns/CultureForge-AI). Add an open-source `LICENSE` before submission; no license is currently declared in this repository.

## Why this is useful

Local founders often have an idea and a target audience but little evidence for choosing a concept, neighborhood, or experience. CultureForge gives them a fast way to explore cultural fit using Qloo's real data. Its intended users are independent founders, local business teams, and cultural strategists evaluating an early concept.

The central idea is to make the agent test its own proposal. It gathers evidence, composes directions, exposes the basis for each one, and runs a challenge that may change the ranking or return a contested or unproven result. Users can remove a venue and rebuild from the remaining evidence, or hold a direction to another returned place to see how the assumption changes.

## What judges can try

1. Open the studio and enter a business idea, audience, location, and budget.
2. Review the resolved audience signals and the Qloo venues behind the three proposed directions. Open a venue's provenance to inspect the workflow, request, response excerpt, and timing.
3. Follow the agent trace: which question it asked, which named workflow it used, what evidence came back, and what remains unknown.
4. Put a direction on trial. Inspect its claim, falsifier, policy version, and scoped verdict. Try changing the anchor or removing a venue and recomposing; the evidence dependency should visibly change.
5. Open **Investigate** to ask a direction a follow-up question, or use the scenario lab to compare audiences with Qloo.

The exact output depends on live Qloo data. If Qloo cannot resolve the brief, the service reports the limitation and offers a way forward; it never substitutes mock evidence. Cached results are identified as cached and cost no new Qloo request.

## Why the agent is central

The agent is the product's decision loop, not a chat layer placed over a dashboard:

```text
founder brief
  → resolve cultural signals and gather Qloo evidence
  → choose the unanswered question for a direction
  → call a named, typed Qloo workflow
  → inspect the returned evidence and limits
  → compose or challenge a direction
  → show the trace, citations, and next useful action
```

The workflow tools are bounded and typed. The agent cannot turn missing data into a fact, invent a score, or quietly pass a malformed request. Qloo selects the evidence; deterministic rules decide which evidence supports a concept and the challenge verdict. Optional Frontier AI through **Vercel AI Gateway** helps phrase direction names and analyze the evidence already on screen. It does not select or fabricate Qloo facts. All model requests go through Vercel; the key is server-side, and unavailable model output leaves the rule-based result intact.

## What makes the evidence trustworthy

- Every direction cites the places and signals used to build it.
- The challenge states its scope: anchor fit within the retrieved sample, not market demand, competition, rent, or willingness to pay.
- The verdict can disagree with the composer. A partial check is `unproven`, and a changed anchor is identified without implying the concept was recomposed.
- Removing a place rebuilds the answer from the remaining evidence, including its description, photograph, citations, and anchor.
- Qloo's returned numbers are shown as returned. CultureForge does not create audience-fit percentages or treat absence from a bounded comparison as proof of exclusivity.
- Errors, empty results, exhausted budgets, and missing photographs have explicit states and next steps.
- Server evidence is cached for 24 hours and the browser holds the composed answer for 12 hours. Reusing a held answer spends no upstream request.

## Tech

- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **API:** FastAPI with typed Pydantic contracts
- **Cultural data:** Official Qloo Hackathon Kit harness (`find_tags`, `recommend`, and named follow-up workflows)
- **Agent and decision logic:** typed investigation loop, evidence store, concept composer, and challenge policy
- **Optional model calls:** Vercel AI Gateway only; model identity is configured server-side
- **Persistence:** SQLite platform layer plus a durable local evidence cache

## Run locally

Requires Node.js 22.19+ for the Qloo harness and Python 3.10+.

```bash
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Install and configure the official Qloo harness with a hackathon key:

```bash
npm install --global @qloo/qloo-harness
qloo setup --qloo
qloo config set base-url https://hackathon.api.qloo.com
qloo doctor --network
```

The Qloo credential belongs in the harness's private configuration (or a server-only environment variable), never in Vite variables or source control. `.env.example` documents optional Frontier AI settings for Vercel AI Gateway. Keep the gateway key private and set `AI_GATEWAY_ENABLED=true` only when you want the optional naming/analysis features.

Start the API and frontend in separate terminals:

```bash
uvicorn backend.main:app --reload --port 8000
npm run dev
```

Open the Vite URL printed by the frontend. The studio is at `/studio/`. Check Qloo configuration without making a request with `python3 scripts/check_api.py`; add `--live` only when you intend to spend one Qloo request. Check Vercel configuration without a model request using `python3 scripts/llm_check.py`; add `--live` to make exactly one model request.

## Quota and limitations

Qloo's hackathon quota is finite and its published limits may change. The backend checks local per-hour and per-day budgets before sending requests, avoids blind retries, and caches successful evidence. Do not raise the caps to work around provider failures. Reuse held evidence during a judge demo.

CultureForge evaluates cultural fit within the evidence Qloo returned. It does not establish market size, customer demand, profitability, legal compliance, or individual preferences. Its concepts are starting points for investigation, not validated business advice.

## Development checks

```bash
npm run build
python -m pytest backend/tests
node scripts/verify_contracts.mjs
```

## Hackathon submission checklist

- [x] Public source repository
- [ ] Externally hosted, working demo URL
- [ ] Open-source license in the repository
- [x] Functional product centered on Qloo cultural data
- [x] Clear target user, problem, and evidence-led agent workflow
