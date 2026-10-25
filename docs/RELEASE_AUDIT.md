# Product and commercial readiness — 23 October 2026

**Superseded for submission readiness by the [25 October final audit](FINAL_SUBMISSION_AUDIT.md).**
The deployment and owner-declaration blockers below are historical; the public
home-PC deployment now passes release and smoke checks.

Later judge-scenario verification and the Berlin retrieval fix are recorded
in [JUDGE_SCENARIOS.md](JUDGE_SCENARIOS.md): 444 backend tests now pass, the
full Berlin flow completes, and the trial library contains 14 briefs.

## What changed

- A specific initial buyer: hospitality agency strategy teams with recurring
  concept reviews. The business model defines a scoped pilot, a proposed price,
  cost constraints, an interview plan and paid-continuation gates.
- The landing Pilot page describes that offer and downloads a discussion brief
  from buyer-entered fields. It sends no inquiry, takes no payment and makes
  no promise of activation. Replaced the misleading Case Studies label with
  Evidence test; that view contains methodology, not customer case studies.
- The decision notebook now captures owner, review date and a team-set spending
  cap, saves them locally and includes them in Markdown export. Existing notes
  remain readable. Notes remain distinct from Qloo facts and verdicts.
- The investor brief supplies a concise pitch, demonstration, proposed use of
  $25,000, validation milestones and candid answers about the risks.
- The contract check now recognises fields already consumed by the studio,
  rather than incorrectly reporting them as ignored.

## Verification environment and results

Used an isolated FastAPI service on `127.0.0.1:8011`, with separate cache and
SQLite files under `/private/tmp`. `QLOO_LIVE_ENABLED=false`,
`AI_GATEWAY_ENABLED=false` and `GEOCODING_ENABLED=false` prevented fresh
upstream requests. The existing configured profile was retained. Prepared
responses came from the shipped real Qloo evidence pack, not fixture answers.
The original application server on port 8000 did not answer a ten-second
health probe; it was left untouched. An initial contract run could not connect
to that server; the isolated run below succeeded.

| Check | Result |
| --- | --- |
| Backend suite | 430 passed; existing FastAPI startup deprecation warnings |
| Production build | Passed; existing large lazy map bundle and mixed import warnings |
| ESLint | Passed |
| Frontend unit checks | Passed; portable records, notebook compatibility, evidence removal, map and interpretation guards |
| HTTP contracts | Passed against the isolated server |
| HTTP walkthrough | 61 checks passed, including research, citations, recompose, verdicts, re-anchor, comparison, ranking and snapshot reopen |
| HTTP endpoint suite | 71 checks passed across 28 endpoint combinations |
| Local smoke | Passed; all 11 prepared examples held; replay spent zero upstream requests |
| Submission packaging | Passed; this does not certify a public deployment |
| Strict release check | Failed as expected: missing public HTTPS demo URL and two owner declarations |
| Browser pilot journey | Form entered with test data; download success shown; studio entry and held Tokyo bakery example opened |
| Browser notebook | Owner, date, cap and criteria saved and recovered after reopening; observations left blank |

These results establish offline and held-evidence behavior. They do not
establish fresh Qloo availability, current model behavior, arbitrary city
coverage, public uptime, payment readiness or customer adoption. Existing live
observations are documented separately in `LIVE_MATRIX.md`.

## Outstanding release and business gates

1. **Public hosting:** `submission.json` has no public demo URL. Deploy the
   single-service build, record the stable HTTPS URL and verify from a clean
   browser and a separate network. Do not submit a local address.
2. **Owner declarations:** eligibility and asset-rights confirmations remain
   false. They require the owner's actual review; they were not checked on
   the owner's behalf. Run `npm run check:release` after completing them and
   recording the URL.
3. **Commercial data access:** get written Qloo terms and costs covering the
   proposed usage, caching, exports and any resale before accepting payment.
4. **Customer proof:** no paid pilots, ROI or repeat purchases are established.
   Conduct the interviews and pilots in `BUSINESS.md`; do not present targets
   as results.
5. **Production controls:** authentication, tenant isolation and data retention
   controls must precede client-sensitive commercial use. Existing anonymous
   studio and issued keys are not a complete enterprise security system.

The event rules and overview were checked on 23 October 2026. Submission closes
30 October at 11:45 pm EDT (31 October at 9:15 am IST). The currently published
rules list judging 2–5 November and an announcement around 5 November; keep the
demo available through judging and recheck for changes. The overview announces
a separate discretionary $25,000 investment, without terms here. Neither a
prize nor an investment can be guaranteed.

Sources: [official rules](https://qloo.devpost.com/rules),
[event overview](https://qloo.devpost.com/).

## Local knowledge maintenance

Refreshed the AST graph and exported the Obsidian vault. Graphify reports a
partial parse of the existing `src/App.tsx` around line 669 and hub-derived
names after communities changed. The TypeScript production build succeeds;
this is a graph extractor limitation. Treat graph answers about that area as
incomplete and check the scoped source. New business documents have not had
an LLM semantic graph extraction; read those documents directly.
Vault export preserved the pre-existing `view.md` and `.obsidian/graph.json`
instead of overwriting them, as reported by Graphify.
