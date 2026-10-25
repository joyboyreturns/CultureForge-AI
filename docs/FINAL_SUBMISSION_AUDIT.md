# Final submission audit — 25 October 2026

The submission target is the home PC, not the Mac development environment.
The patched application is deployed there and the exercised release paths pass.
This is evidence of readiness, not a guarantee of a prize or of no undiscovered bugs.

## Deployed version

- Public demo: <https://cultureforge-ai.tail601a7c.ts.net>.
- Application version `0.3.0`; composer `5`; policy `anchor-fit-5`.
- Runtime fixes are in `1f81966` and `8abed1a`; test isolation and secret-file
  safeguards are in `4ee11af`. Later audit-document commits do not change the image.
- The deployed service passes health and public smoke checks after replacement.
  Its investigation source matches the updated checkout. Existing saved data
  was retained, and the previous image was preserved for rollback.

## Fixes made

1. Investigation replay no longer gives old evidence a new acquisition time or
   reports its original request duration as current wait time. It retains the
   acquisition time, reports zero replay duration, and states the original
   duration separately. Two regression tests cover replay and recovery when
   one facet fails.
2. Updated Vite to `6.4.5` and its compatible React plugin to remove the Vite
   and esbuild development-server advisories. Updated the image's pip installer.
3. Replaced the README and submission draft's obsolete “not deployed” claims,
   added the working public link, and corrected the trial count to 14.
4. Corrected singular/plural wording in the model-rejection explanation.
5. Made the mocked geocoder cache test independent of the operator's geocoder
   kill switch. Broadened `.gitignore` to protect `.env` backup files, while
   keeping `.env.example` tracked. Server-only files were preserved.

## Verification

| Check | Result |
| --- | --- |
| Home-PC backend suite, production Python runtime, network disabled | **447 passed** |
| Home-PC final production image build | Passed |
| Production image: all 14 prepared trials across five business categories | Passed; citations, evidence removal, verdicts, PDF responses, zero upstream requests |
| Production image: full HTTP walkthrough | **61 checks passed** |
| Production image: HTTP endpoint suite | **71 checks passed across 28 endpoint combinations** |
| Production image: frontend/backend HTTP contracts | Passed |
| ESLint, TypeScript, production build, frontend unit checks | Passed locally; GitHub Actions also passed on Linux |
| Public strict release check after deployment | Passed |
| Public smoke after deployment | Passed; 14/14 trials held, checked answer has two directions and zero upstream requests |
| Installed Python packages in final production image | pip-audit: **no known vulnerabilities found** |
| JavaScript production dependencies | npm audit: **no known vulnerabilities found** |
| Tracked-text secret-pattern scan | No candidate credential/private-key matches; no tracked `.env` or environment-backup history found |
| Browser journey on public deployment | Landing → studio → Tokyo example → evidence test → map; no account required |
| Evidence test in browser | Lead anchor contested, alternative direction unproven; leading direction changed |
| Hosted map | Nine Tokyo venues listed as plotted; one explicitly unplotted; address-match provenance shown |
| Export layout | Inspected all five rendered pages of a real held-evidence Brooklyn PDF; no observed clipping or overlap |
| Video access | YouTube opens signed out, correct title, playable, duration 3:39 |

The Docker replay used an empty temporary data volume, a non-secret placeholder
credential, disabled Qloo/model/geocoding switches and **no network**. It tested
the final image before replacing the public service. It did not borrow the
live server's private cache. The post-deployment smoke test did not increase
the Qloo request count.

Detailed logs and deployment metadata are retained locally and excluded from
the public repository. This document contains only the submission-readiness summary.
Linux CI for the final source/test changes passed:
<https://github.com/joyboyreturns/CultureForge-AI/actions/runs/40207772611>.

## Remaining limits and owner actions

- **Three moderate npm advisory entries remain in build-time Tailwind/PostCSS
  dependencies**, from one selector-parser advisory. They are excluded from the
  production runtime. npm's supported automated remedy is a breaking Tailwind
  4 migration; that migration was not made during final submission validation.
- Existing FastAPI lifecycle/test-client deprecation warnings and the large,
  lazily loaded MapLibre bundle warning remain. They did not fail validation.
- Arbitrary new briefs, fresh upstream Qloo/model availability, Safari behavior,
  public uptime through judging and every possible input are not certified by
  these held-evidence checks. No new live retrieval was deliberately requested.
- Video playback/access was sampled, not a full audio/editorial review. YouTube
  exposed no selectable captions during inspection; check the final edit's
  burned-in captions or upload an accurately timed caption track if needed.
- Keep the home PC, Docker service and Funnel online through judging. Verify
  the URL once from a phone on mobile data with Tailscale off; this audit
  verified Funnel configuration and public responses but did not operate a
  separate physical network.
- Push/pull of the audit fixes and deployment are complete. The Devpost URL is
  still blank in `submission.json`; submit the project on Devpost and record
  its resulting URL. The existing owner eligibility/asset-rights confirmations
  were retained, not made on the owner's behalf.

## Judging assessment

The strongest demonstrated distinction is evidence that can change or reject
a direction, with traceable Qloo use and a usable public app. Technical feature
count alone cannot establish a winning probability. No customer adoption,
willingness to pay, measured commercial impact or comparison with the full
current field has been established.

The [official rules](https://qloo.devpost.com/rules) and
[event overview](https://qloo.devpost.com/) were rechecked on 25 October 2026.
Technical implementation, design, potential impact and idea quality are equally
weighted. The published deadline is **31 October 2026, 9:15 am IST**
(30 October, 11:45 pm EDT). The overview says the top three finalists must be
available for preparation and a live appearance on **5 November**.
