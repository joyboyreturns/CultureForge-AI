# Who pays, and why

This page states the commercial case as **assumptions to test**. None of it is
measured. No customer, revenue, conversion or market-size figure appears here,
because none has been observed. Each assumption below says how it would be
checked.

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

## Pilot pricing logic (a structure, not a price)

No price is proposed here, because none has been tested. The structure a
pilot price should follow:

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

## What would change this

- If A2 fails (polish beats traceability), the defensible feature becomes a
  liability for the sale, and the buyer is likely the wrong one.
- If commercial Qloo access is priced per call above the A1 value ceiling, the
  held-evidence cache and prewarming become the product's margin, not just a
  demo convenience.
