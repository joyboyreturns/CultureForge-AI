# Three-minute demo script

Record this on the **hosted** URL after `RUN_PROFILE=judging` and a prewarm
([JUDGING_DAY.md](JUDGING_DAY.md)), with `AI_GATEWAY_ENABLED=true`. The agent
loop and *Ask the evidence* need the model; everything else does not. Use the
first prepared brief: it is prewarmed, so nothing on camera waits on Qloo.

Button and tab names below are exactly as they appear in the build.

| Time | Show | Click / say |
| --- | --- | --- |
| 0:00–0:20 | **Problem.** Landing page. | Say: *"A strategist choosing a concept for a neighbourhood needs an argument a committee can check, and a chance to be told it's wrong."* Scroll once. |
| 0:20–0:45 | **Live brief.** | Click **Run the example and evidence test**. Point at the *Held evidence · no new Qloo call* label, the three directions, and the *anchor fit* verdicts arriving, including one **contested**. Click **Open this brief in the studio**. |
| 0:45–1:10 | **Three directions.** Studio results. | Point at a direction card and click **Why this direction?**: every decision lists the Qloo evidence it cites. Open the **Beyond places** tab: artists, films and brands for the same audience tags, with no location. |
| 1:10–1:35 | **Evidence inspector.** | In the place strip, click a place to open its provenance: the Qloo workflow, the allowlisted request, the entity ID and the returned excerpt. Close it. Open the **Interest map** tab, click **Map interest cells**, and say: *"interest cells, not venue pins."* |
| 1:35–2:05 | **A test that can say no.** | Show **Evidence test profile** (the profile is visible before the test, and changeable). Click **Test the evidence**. Expand the **contested** direction: the claim, what would contradict it, the rank band, *Confidence*, and the leave-one-out line. Click a place under **Test against another place** and watch the verdict move. |
| 2:05–2:30 | **Agent trace.** | Scroll to the research agent card: each step's tool, why it was chosen, and what Qloo returned; then the analysis, where every claim carries its Qloo IDs, and *N claims rejected by the citation check*. |
| 2:30–2:50 | **Chat.** | In **Ask the evidence**, click the first starter question. Then type *How many visitors a day will this get?* and show the refusal. |
| 2:50–3:00 | **Deliverable.** | Click **PDF report** and open the PDF: cover, directions, verdicts, the evidence table with Qloo IDs, and the limits page. End on the scope line. |

## If something misbehaves on camera

- **No agent card, or "rules answer stands".** The model is off or its
  allowance is used up. Say so: the rule composer's answer is the fallback.
  Then move on.
- **Ask the evidence returns a 503.** The model gateway is off. Show the
  message; it is the designed behaviour.
- **A brief shows "Live lookup".** It is not prewarmed. Use a brief marked
  **Evidence held**, or prewarm it again.
