# Who pays, and why

CultureForge sells a defensible cultural argument for a hospitality concept review.
The first buyer is a strategy lead at a hospitality brand agency with recurring
client briefs. Expansion to multi-site operators follows proof of repeat use.
The commercial claims and prices below are **hypotheses to test**, not traction.
No paying customers, revenue, measured savings or market size have been established.

## The buyer

**Primary buyer:** location and concept strategists at hospitality and retail
groups (operators with more than one site) and at the brand and experience
agencies that advise them.

**The job they are paid to do:** before a group commits to a site, a format or
a brand extension, someone has to argue which concept fits which
neighbourhood and audience, and defend that argument to an investment
committee or a client.

**What CultureForge gives them** (each item is a feature in this repository):

| They need | CultureForge does |
| --- | --- |
| A concept grounded in what a local audience is drawn to | Directions composed from Qloo places and audience tags, with every decision citing the evidence behind it |
| To know when the argument is weak | An evidence test (policy anchor-fit-5) that can return *contested*, with a stated confidence and sensitivity |
| Something that can't be argued away as invention | Provenance for every Qloo request, no invented scores, and claims from the model rejected unless they cite observed Qloo IDs |
| A deliverable for a committee or client | A PDF with seeds, directions, verdicts, an evidence table with Qloo IDs, and stated limits |
| Follow-up questions without a new brief | *Ask the evidence*, which answers from the held evidence or refuses |

**Who does not pay:** the independent first-time founder. CultureForge still
works for them, but the assumption is that they will not pay for evidence
packaging at the price a licensed data source requires.

## How this work is done today (assumed, to be confirmed in interviews)

| Today | Where it falls short | What CultureForge changes |
| --- | --- | --- |
| Desk research: site visits, social listening, competitor lists, consultant intuition | Slow to repeat for each candidate site; the reasoning is hard to audit | Each brief is rerun in minutes from held evidence, and every claim is traceable |
| Syndicated demographic and footfall data | Says who is nearby, not what they are culturally drawn to | Qloo affinity over places, tags and other domains (artists, films, brands) |
| General-purpose AI chat | Fluent and unsourced; numbers cannot be traced | Model output is validated against observed Qloo IDs, and numbers come only from Qloo |

CultureForge **complements** footfall, rent and demand analysis. It does not
replace them, and it says so on every verdict.

## Assumptions to test

| # | Assumption | How it would be checked |
| --- | --- | --- |
| A1 | Strategists spend significant time assembling the cultural argument for a site or concept | Five to eight interviews with strategists; time-diary one live project |
| A2 | Traceability matters more to them than polish: they will prefer a cited, falsifiable direction over a fluent one | Show both versions of the same brief; record which they would take to a committee |
| A3 | A *contested* verdict is useful rather than unwelcome | Observe reactions to a contested result on their own brief |
| A4 | The PDF is close to a client-ready deliverable | Ask them to send it as-is; record every edit they make first |
| A5 | Budget sits with the strategy team or the agency engagement, not with IT | Ask who signed the last research-tool purchase |

## The first offer

**Proposed design partner pilot: $1,500 USD, 30 days, one team, five scoped briefs.**
One brief means one idea, one audience and one city. Include one onboarding
session, five cited evidence briefs, one concept review and a field experiment
plan. Agree refresh, comparison, support and workflow limits before kickoff.
This is a pricing experiment, not a currently available paid subscription.

The public Pilot page creates a downloadable discussion brief with the buyer's
decision and acceptance criteria. It sends no inquiry, books nothing and takes
no payment. The existing studio supplies the research, evidence tests, PDF,
share links and decision notebook; onboarding and the review are founder-led
services to validate before automating them.

**Continuation hypothesis:** $750 USD per team per month for up to five scoped
briefs, with usage and support caps agreed in the contract. No unlimited plan.
This is not implemented billing. Offer it only if observed willingness to pay,
repeat usage and the commercial data quote support the cost floor below.

## Pilot pricing logic

The proposed price must pass both constraints; lower the scope or stop if it
cannot. Do not assume the hackathon key grants commercial usage rights.

```
pilot price  >=  (Qloo licence share + model calls + hosting) per brief  x  briefs in pilot
                 + onboarding time
pilot price  <=  value of strategist time saved per brief  x  briefs in pilot
```

- **Cost floor.** The inputs are all observable in this codebase.
  `/api/health` reports Qloo and model call counts, and a brief's delivery
  reports the upstream requests it cost. Multiply by the commercial Qloo and
  model rates once they are known.
- **Value ceiling.** The input is the A1 interview result: hours per brief
  multiplied by the buyer's loaded hourly cost.
- **Pilot shape (assumption).** A fixed number of briefs for one team over a
  fixed period, with a review against A2–A4 at the end. A per-workspace key
  and usage metering already exist (`backend/platform.py`).

Cache hits lower transport consumption; they do not eliminate a fixed data
licence fee. Meter every workflow, including comparisons and optional agent
steps. A brief is not guaranteed to cost two calls. Local call counts are not
an invoice, and model-off replay does not establish production model costs.

**Illustrative planning scenario, not measured economics:** at a $1,500 pilot
price, a 60% contribution-margin target permits at most $600 in direct delivery
costs. If onboarding and review take four hours valued internally at $75/hour,
$300 remains for the allocated data licence, model, hosting and other direct
costs across five briefs. Replace these assumptions with actual quotes and
time logs. If the costs exceed that allowance, renegotiate scope or price
before accepting a pilot. This target is not a demonstrated margin.

## First customers and a decision to continue

1. Founder identifies 20 hospitality brand agencies with recurring concept
   work. Outreach must be sent by the founder; none has been sent by the app.
2. Conduct eight problem interviews. Ask about the last review, existing
   workflow, evidence gaps, time spent, purchasing owner and budget authority.
   Do not count enthusiasm as demand.
3. Invite three teams to scope a design partner pilot using one of their own
   real briefs. Show an unproven or contested result as well as a supported one.
4. Agree the acceptance criteria, baseline task and cost cap before delivery.
   Record who used the output, edits required, time before and after, and what
   was actually decided. The notebook records owner, review date and spending cap.
5. Proposed continuation gate: at least two teams pay the agreed pilot price,
   use the export in a real review, and at least one purchases a second period
   within 60 days. These are targets, not results. Rework the offer if they fail.

## Why this could remain useful

Qloo supplies the licensed taste graph; CultureForge owns the workflow for
turning it into an inspectable, challengeable and reusable decision record.
Generic chat can draft concepts. This product adds bounded evidence retrieval,
anchor tests that can fail, removal and recomposition, and cited deliverables.
No exclusive access to Qloo, proprietary dataset or proven moat is claimed.
Longer-term differentiation would require demonstrated reviewer adoption and,
with customer permission, learning which experiments lead to useful decisions.

## Commercial readiness gates

- Obtain a written Qloo commercial quote and confirm permitted storage,
  retention, display, export and any resale or sublicensing terms.
- The studio is an anonymous hackathon experience. Issued keys and SQLite
  metering are foundations, not a complete multi-tenant enterprise product.
  Authenticate users, verify tenant isolation, establish deletion and retention
  policies, and agree support and availability before hosting client-sensitive work.
- Implement billing only after the price and delivery cost are validated.
- Do not sell cultural affinity as demand forecasting or site underwriting.

See [INVESTOR_BRIEF.md](INVESTOR_BRIEF.md) for the pitch, proposed use of funds
and validation milestones.

## What would change this

- If A2 fails (polish beats traceability), the defensible feature becomes a
  liability for the sale, and the buyer is likely the wrong one.
- If commercial Qloo access is priced per call above the A1 value ceiling, the
  held-evidence cache and prewarming become the product's margin, not just a
  demo convenience.
