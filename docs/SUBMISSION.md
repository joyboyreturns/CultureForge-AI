# Submission

For the [Qloo Agentic Hackathon](https://qloo.devpost.com/). The dates below
come from an audit of the [rules](https://qloo.devpost.com/rules) on 21 October
2026. **Recheck them on the official site before submitting.** That audit read:
submissions close **30 October 2026, 11:45 pm EDT** (31 October, 9:15 am IST),
and judging access is needed until **16 November 2026, 11:45 pm EST**. It
found no required demo video for this event; recording one is still advised
(see [DEMO.md](DEMO.md)).

## Release checklist

| Requirement | Status in this repository | Owner action |
| --- | --- | --- |
| Working Qloo agent application | Implemented and tested with fixtures | Deploy, prewarm, and click through the hosted URL |
| Public, usable demo | Docker service, compose file and Render blueprint provided; **not yet deployed** | Follow [DEPLOY.md](DEPLOY.md); record the URL in `submission.json` and Devpost |
| Open-source licence | MIT `LICENSE` at the root | Push and confirm GitHub shows MIT |
| Description | Draft below | Paste it, then check every sentence against the deployed build |
| Eligibility and asset rights | Need your personal confirmation | Review the rules and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md); set the two confirmation fields in `submission.json` |
| Judges can use it without an account | The studio has no login | Check it in a private window on the hosted URL |

## Devpost text

**Name:** CultureForge AI

**Tagline:** Concept directions that have to survive their Qloo evidence.

### Inspiration

Hospitality and retail groups, and the agencies that advise them, have to
argue which concept fits which neighbourhood before they commit to a site. A
fluent idea is cheap. What is expensive is an idea nobody can trace, or one
that was never given the chance to be wrong.

### What it does

A strategist enters a business type, an audience, a location and a budget, or
picks one of eight prepared briefs. CultureForge:

1. resolves the audience into Qloo tags, retrieves up to ten local places, and
   sends the same tags to other domains (artists, films, brands) with no
   location;
2. composes up to three business directions, and every decision names the
   Qloo evidence it came from;
3. lets a model agent run up to eight more Qloo workflows to sharpen or
   challenge those directions. The model can only name identifiers it has
   already seen, the server builds every request, and every claim in its
   analysis must cite an observed Qloo entity ID or tag URN, or it is
   rejected;
4. puts each direction on trial (policy *anchor-fit-4*). The verdict can be
   *contested*, and comes with a confidence label and a leave-one-out
   sensitivity check. The demographic profile it ranks against is shown, and
   can be changed, before the test runs;
5. answers follow-up questions (*Ask the evidence*) only from the evidence,
   and refuses questions it cannot answer, such as footfall or demand;
6. exports a client-ready PDF with the evidence table, Qloo IDs, verdicts,
   interest-cell map and limits.

The scope is stated on every verdict: anchor fit within the retrieved sample,
not demand, rent, footfall or willingness to pay.

### How we built it

A React and TypeScript studio talks to a typed FastAPI service. Qloo is
reached through the official Hackathon Kit harness, with one request builder
per workflow, a durable evidence cache, single-flight de-duplication and a
SQLite call ledger. The model layer uses Vercel AI Gateway only, with
schema-checked structured output. A run profile switches between dev budgets
and an unbudgeted judging mode, and keeps timeouts, a cool-down after a 429,
and a kill switch either way.

### How it maps to the judging criteria

| Criterion | What to look at |
| --- | --- |
| **Use of the LLM** | The agent loop (`backend/agent.py`) plans, chooses Qloo workflows, observes the results and writes cited claims. A validator rejects any claim that cites an unobserved ID or states a number of its own. The same validator guards *Ask the evidence* (`backend/chat.py`). If the model fails, the rule composer's answer stands, and the trace says so. |
| **Qloo integration** | All nine harness workflows are used: find_tags, recommend (places and other domains), rank, compare_audiences, entity_tags, where_popular, audience_demographics, trends and describe. Each has its own payload builder, provenance with allowlisted query keys, and caching. |
| **Engineering** | Typed requests (bad input is a 422), one error envelope, no mock path in the product, run profiles, a kill switch, prewarming, a multi-process-safe SQLite ledger, and 200+ backend tests that cannot reach Qloo or a model. CI runs lint, build and tests. |
| **Originality** | The output is designed to be able to say no. A contested verdict reorders the directions, a removed venue rebuilds the answer without it, and a model claim without a Qloo citation is struck out on screen. |
| **Defensibility** | Every number shown is one Qloo returned, every decision cites evidence, every verdict states its policy, scope, confidence and sensitivity, and the PDF carries the Qloo IDs. See [EVIDENCE_POLICY.md](EVIDENCE_POLICY.md) and [LIMITATIONS.md](LIMITATIONS.md). |

### Challenges

Qloo's `rank` returns nothing for a location and tags alone, so the evidence
test ranks against a demographic profile and says so. Entity lists are capped
at ten, which sets the place sample. The hardest product problem was letting
the evidence disagree with an attractive idea, and showing that on screen
rather than hiding it.

### What's next

Test it with strategists on live projects (the assumptions are in
[BUSINESS.md](BUSINESS.md)). Possible next technical steps: a native HTTP
transport in place of the CLI harness, and multi-instance state.

**Built with:** Qloo Hackathon Kit, Python, FastAPI, Pydantic, SQLite, fpdf2,
React, TypeScript, Vite, Tailwind CSS, Vercel AI Gateway.

## Before you press submit

1. Deploy ([DEPLOY.md](DEPLOY.md)), switch to `RUN_PROFILE=judging`, then
   prewarm and smoke-test ([JUDGING_DAY.md](JUDGING_DAY.md)).
2. Click through the [demo script](DEMO.md) on the hosted URL in a private
   window.
3. Record the URL in `submission.json` and run `npm run check:release`.
4. Confirm eligibility and asset rights, push, and submit to the correct event.
