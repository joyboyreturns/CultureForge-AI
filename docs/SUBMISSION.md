# Submission handoff

Prepared on 21 October 2026 for the [Qloo Agentic Hackathon](https://qloo.devpost.com/). Recheck the official site before submitting.

## Release requirements

The [current rules](https://qloo.devpost.com/rules) and [event overview](https://qloo.devpost.com/) govern this entry. Deadline: **31 October 2026, 9:15 am IST** (30 October, 11:45 pm EDT). Keep judging access working through **17 November, 10:15 am IST** (16 November, 11:45 pm EST). The current event does not require a demo video; the 2025 event did.

| Requirement | Repository status | Owner action |
| --- | --- | --- |
| Working Qloo agent application | Implemented; verify production with the walkthrough. | Deploy and rehearse. |
| External usable demo | Deployment packaging provided; not published. | Add the HTTPS URL to submission.json, README and Devpost. |
| Public source and open-source license | Public repository confirmed during audit; MIT LICENSE added locally. | Push reviewed changes and check GitHub detects the license. |
| Description | Draft below. | Paste into Devpost and verify every claim against your deployed build. |
| Eligibility, ownership, third-party rights | Requires personal confirmation. | Review official eligibility and THIRD_PARTY_NOTICES.md; set the two confirmation fields in submission.json only after review. |
| Access for judges | Anonymous studio is implemented. | Check a signed-out/private browser, including API connectivity and quota. |

No checklist can certify eligibility or guarantee an award. Do not tick public deployment until the published app has been tested.

## Devpost text draft

**Name:** CultureForge AI

**Tagline:** Business ideas that answer to their cultural evidence.

### Inspiration

A local founder needs to choose what to try before committing to a lease, a fit-out, or a brand. A fluent business idea is easy to generate. The harder question is which observations support it—and what evidence would make us change our minds.

### What it does

CultureForge is a cultural hypothesis studio for independent founders and experience builders. Enter a business category, audience, location and planning budget. Qloo resolves cultural signals and retrieves real reference places. CultureForge composes directions with decision-level citations and visible assumptions.

Then challenge a direction's anchor. The test can return supported, contested, or unproven, and can change the order of the directions. Hold the same concept to another returned place to inspect the assumption. Remove a venue and rebuild descriptions, photographs, citations and anchors from the remaining evidence. Export or share the exploration with its evidence and recorded verdict.

A replayable guided tour introduces the actual workflow. A decision notebook turns a selected direction into a founder-defined field experiment with proceed/stop criteria and separately labelled observations. Its exported decision record preserves the Qloo basis; it does not present founder notes as provider evidence or validated demand.

The scope stays explicit: anchor fit within the retrieved sample. Cultural affinity does not establish demand, profitability, rent or willingness to pay.

### How it works

The React and TypeScript studio talks to a typed FastAPI service. Named Qloo workflows supply cultural evidence, not illustrative data. A durable cache holds successful workflow answers. The research run exposes retrieval, deterministic composition and, when enabled, a bounded model plan, at most one allowlisted evidence test, and reflection.

Optional model work uses Vercel AI Gateway exclusively. It can name directions, select existing evidence and propose bounded interpretations. Deterministic rules retain factual claims, citations and challenge verdicts. Missing or invalid model output leaves the rule-based result available and records the limitation.

### Why Qloo matters

Without Qloo, CultureForge has no venue evidence, cultural signals or basis for its anchor comparisons. It refuses to replace missing evidence with a fabricated answer. Qloo supplies the relationships; CultureForge makes the resulting proposal inspectable and open to challenge.

### Challenges and accomplishments

We built workflow-specific requests, explicit quota limits, durable evidence caching, and typed contracts across the API boundary. A harder product problem was letting evidence disagree with an attractive idea. The challenge policy distinguishes failed checks from missing checks, labels alternative anchors, and treats incomplete answers as unproven.

### What's next

Test the published workflow with independent founders. Measure whether they can identify a useful next experiment and explain the evidence's limits. Customer validation, commercial demand and a scalable multi-instance deployment remain future work.

**Built with:** Qloo Hackathon Kit, React, TypeScript, Vite, FastAPI, Pydantic, SQLite, Vercel AI Gateway, Tailwind CSS, Lucide.

## Final review sequence

1. Run the checks in README and complete the local judge walkthrough.
2. Confirm media provenance and eligibility. No audited customer traction or performance advantage should be added without evidence.
3. Publish the Docker service with persistent state and private credentials.
4. Record the demo URL in submission.json and README. Run `npm run check:release`.
5. Repeat the walkthrough from a private browser on the public URL. Open its share link in a second browser.
6. Push source, confirm GitHub shows MIT, attach current screenshots, and submit the correct Devpost event.

The draft describes implemented behavior, not a promise that every brief returns three usable directions or every check is available from Qloo.
