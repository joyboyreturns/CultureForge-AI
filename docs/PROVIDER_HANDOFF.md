# Ready-to-send continuation prompt

Copy everything below into the other provider. If it cannot access the local
workspace, clone the public repository. A portable
`artifacts/validation/cultureforge-handoff.bundle` is also available locally.

---

Continue the CultureForge AI hackathon hardening from the completed work below.
Do not restart the audit or rewrite working features. Finish the remaining
release blockers with the smallest safe changes. First inspect `git status`
and the latest commits, preserve unrelated user changes, and read the local
`AGENTS.md` plus `docs/IMPLEMENTATION_REVIEW.md` and `docs/LIMITATIONS.md`.

Repository: https://github.com/joyboyreturns/CultureForge-AI
Local workspace: `/Users/vincent/Documents/CultureForge AI`
Branch: `main`. Starting verified public commit:
`141b33372dd798c3ec920567b70d39da9daf1290`.
The three implementation commits through `026f3d1` were pushed to `origin/main`
on 22 October 2026 at the owner's explicit request; inspect `git log` for the
latest hashes. Release verification still has unresolved external/owner
gates. If using the supplied Git bundle, clone the public repository, inspect
the bundle with `git bundle verify /path/cultureforge-handoff.bundle`, and
fetch it into a new review branch rather than overwriting local changes:

```sh
git fetch /path/cultureforge-handoff.bundle main:codex/cultureforge-handoff
git switch codex/cultureforge-handoff
```

Core commits: `ba94f88` (relevance/composition), `b2b7331`
(research/graph/reliability). The following export/documentation commit is
included in the bundle as well. Validation containers were removed and the
isolated Colima profile `cultureforge-validation` stopped after testing; the
profile and final image remain available for reuse. Default Docker context
was not changed.

## Already implemented and verified

- Separate business-idea input, actual Qloo category-tag resolution and
  documented category filtering; inspectable direct/indirect relevance and
  geography assessments. Indirect references cannot anchor a direction.
- Removed broad recipe fallback and generic design triggers. Tokyo bakery
  now has two hypotheses: morning collection and craft discovery. No padding
  to three directions; irrelevant held samples can produce no direction.
- Early deterministic research preview and actual milestone timings;
  polling reconnection and browser reload resume the same server process's
  job. Interactive source-to-direction graph uses existing citations, with
  explicit interpretation edges and source-removal/recomposition.
- Removed synthetic progress percentages. Recorded replay states its real
  acquisition time and composer version. Applying source removal rebuilds
  anchors, descriptions, photographs and citations and clears stale analysis.
- Agent prompt/validation version `agent-loop-3` withholds comparative winners
  unless a completed comparison with returned rows supports comparison.
  Citation checks remain bounded validation, not full semantic entailment.
- Evidence-test policy `anchor-fit-5`, requested/distinct ranking rows,
  meaningful sample requirement, independent checks and explicit completion
  states. Supported, contested, missing and partial cases have test fixtures.
- Cache single-flight/persistence fixes, replay fingerprint fixes, CORS and
  API method handling. Real Linux PDF bug fixed: Droid CJK font lacked Latin,
  so PDFs now use a Latin primary plus CJK fallback. Docker installs both.
- Reviewed official rules and previous 2025 winners. Four criteria carry
  25% each. Deadline October 30, 2026, 11:45 pm EDT / October 31, 9:15 am IST.
  Competitor claims are author descriptions/README inspection, not source
  audits or live tests. Internal estimate approximately 6.8/10, not a promise.

## Evidence and validation

See `artifacts/validation/` and the review for exact commands and conditions.
macOS backend: 288 passed, 81% coverage. Build, lint, frontend unit checks,
HTTP contracts, walkthrough (61/61), endpoints (71/71) and smoke passed.
Linux backend: 288 passed, 81% coverage (`docker-pytest.log`). The isolated VM
was Ubuntu 24.04.4, running the actual Debian Bookworm/Python 3.12 image.
Container startup, held-data smoke and Qloo harness import passed. English
and Japanese were visually inspected together on four actual PDF pages.
Mobile/browser-matrix validation is incomplete.

Actual Tokyo Qloo + Vercel checks already ran; do not spend more calls merely
to repeat them. Category-filtered direct generation took 11.102 s with one
new recommendation workflow. Bounded two-step research observations took
40.267 s and 62.284 s with held Qloo evidence and actual model requests.
First evidence/concept in the latter observation: 6/8 ms. Production still
allows eight steps: these are not cold-run or full-default timing claims.
The user's earlier ~286 s was not independently timed as a controlled baseline.

`tokyo-research.json` revalidates the authentic model response under the final
comparison guard: four cited statements retained, one comparative statement
rejected, no preferred winner. Separate pre-guard files preserve the original
output. Post-response revalidation was not a newly executed API run.
Other actual held briefs include one-direction and zero-direction Brooklyn
answers, plus an uncached London error with live retrieval disabled.

The local platform has the recorded exploration `exp-e2d436d28d8767a3`.
Platform DB, evidence cache and secrets are not committed or in the bundle;
a fresh host will need deliberate prewarming or an explicitly authorized
private data migration. JSON validation artifacts are audit records, not a
new mock-provider path or an automatically installed replay.

## Remaining work, in priority order

1. **Public deployment and owner attestations.** No public deployment was
   purchased or verified. `submission.json` has an empty public URL and false
   owner eligibility/asset-rights confirmations. `npm run check:release`
   deliberately fails those three checks. Obtain the owner's actual
   attestations; never set them true on their behalf. Render's configured
   persistent-disk plan costs money: obtain approval before provisioning a
   paid service. Prepare configuration first; keep secrets server-only.
2. **Dependency advisories.** `npm-audit.json` reports 9 development-tool
   advisories (6 high, 3 moderate, no critical). Suggested fixes include major
   Tailwind/Vite changes. Evaluate and test a safe upgrade separately; do not
   run `npm audit fix --force` blindly. Static runtime excludes frontend dev
   dependencies; that does not prove every runtime dependency safe.
3. Verify the final hosted URL from a clean browser, actual persistence after
   restart, and selected replay/held-brief availability. Prewarm only selected
   briefs with explicit live execution; do not repeatedly fetch all samples.
4. If time remains, test full mobile/browser coverage and an explicitly
   budgeted cold research run. Improve generic category composition only
   with supporting evidence. Customer impact remains unvalidated.
5. Rerun checks affected by further edits, inspect secrets/diffs, commit
   coherently and push `origin/main` only after the applicable verification
   passes and no unrelated changes are present. Report remaining limits.

## Constraints to preserve

- Never fabricate Qloo rows, IDs, metrics, citations, progress, agent actions
  or positive verdicts. Query seeds are not measured audience preferences.
  Venue absence from a bounded response does not prove exclusivity.
- Read scoped graphify/vault retrieval first when available; never load the
  whole graph or vault. Refresh AST graph/vault after substantial changes.
  They are local-only and excluded from Git. On a new clone, follow AGENTS.
- Do not delegate without explicit user permission for that specific scope.
- All model traffic remains in `backend/llm.py` through server-only Vercel
  AI Gateway credentials. Do not add a provider or frontend credential.
- Do not print/commit `.env`, `~/.qloo/config`, keys, salts or private DBs.
  Existing local `.env` was already in judging mode; do not change profile or
  raise budgets to bypass failures. Preserve finite quota, cache, pacing,
  kill switch and request builders through `run_workflow_cached`.
- No mock data in the studio. Mock provider is explicit pytest-only setup.
- Research jobs remain single-process memory; reload resume does not survive
  a server restart. No cancellation or distributed job store was added.
- An original user server on port 8000 was left untouched. The validation
  preview uses port 8012 with model and live Qloo disabled. Do not kill a
  process simply because it occupies a port.

The mission is stronger, credible judging performance, not a first-place
promise. Complete the actual release gates, then give concise evidence-backed
results and any remaining limitations.
