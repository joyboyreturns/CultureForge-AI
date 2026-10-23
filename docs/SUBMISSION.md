# Submission

For the [Qloo Agentic Hackathon](https://qloo.devpost.com/). The
[official rules](https://qloo.devpost.com/rules), checked on 23 October 2026,
set the deadline to **30 October 2026, 11:45 pm EDT** (31 October, 9:15 am IST).
They currently state judging on **2–5 November**, with winners around
5 November. Keep the service accessible through judging and recheck the rules
before submission. A video is optional. A working public demo, public source
and a detectable open-source license are required.

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

A strategist enters a business category, a specific business idea, an audience, a location and a planning budget, or
picks one of three prepared briefs that open instantly from held Qloo evidence. CultureForge:

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
4. puts each direction on trial (policy *anchor-fit-5*). The verdict can be
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

| Official criterion | Weight | Evidence to inspect |
| --- | --- | --- |
| Technological Implementation | 25% | Cached Qloo workflows, category resolution, bounded controller, typed APIs, comparison guards and actual Linux container checks. |
| Design | 25% | Progressive real results, source-to-decision graph, honest replay labels, recoverable failure and empty states. |
| Potential Impact | 25% | A specific strategy workflow and useful exports; customer adoption and commercial value remain unvalidated. |
| Quality of the Idea | 25% | A proposal that can be challenged and recomposed when evidence is removed, rather than another untraceable idea generator. |

These weights come from the official rules. Estimated scores in
[IMPLEMENTATION_REVIEW.md](IMPLEMENTATION_REVIEW.md) are internal estimates,
not official judging results.

### Challenges

Qloo's `rank` returns nothing for a location and tags alone, so the evidence
test ranks against a demographic profile and says so. Entity lists are capped
at ten, which sets the place sample. The hardest product problem was letting
the evidence disagree with an attractive idea, and showing that on screen
rather than hiding it.

### What's next

Test a proposed $1,500, 30-day design partner pilot with hospitality agency
strategy teams: five scoped briefs, a concept review and a field experiment
plan. The Pilot page prepares a downloadable discussion brief; the experiment
notebook captures an owner, review date, spending cap and proceed/stop criteria.
Pricing, willingness to pay and delivery economics remain unvalidated.
Commercial Qloo terms are required before accepting a paid pilot. The
[business model](BUSINESS.md) defines customer interviews and repeat-purchase
gates; the [investor brief](INVESTOR_BRIEF.md) proposes milestones for a
$25,000 investment. Production authentication and tenant isolation precede
client-sensitive use.

**Built with:** Qloo Hackathon Kit, Python, FastAPI, Pydantic, SQLite, fpdf2,
React, TypeScript, Vite, Tailwind CSS, Vercel AI Gateway.

## Before you press submit

1. Deploy ([DEPLOY.md](DEPLOY.md)), switch to `RUN_PROFILE=judging`, then
   prewarm and smoke-test ([JUDGING_DAY.md](JUDGING_DAY.md)).
2. Click through the [demo script](DEMO.md) on the hosted URL in a private
   window.
3. Record the URL in `submission.json` and run `npm run check:release`.
4. Confirm eligibility and asset rights, push, and submit to the correct event.
