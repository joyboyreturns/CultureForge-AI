# Judging-day runbook

Everything here uses the deployed service from [DEPLOY.md](DEPLOY.md). Replace
`$HOST` with its HTTPS URL.

## Before judging opens

1. **Check the profile.** The Render blueprint already deploys with
   `RUN_PROFILE=judging` (keep `QLOO_LIVE_ENABLED=true`). On another host, or
   after testing with `dev`, set it in the environment settings and restart.
   No code change is needed.
2. **Check health.**

   ```bash
   curl -s $HOST/api/health
   ```

   You should see `"profile": "judging"`, every limit under `budgets`
   reported as `"unlimited"`, `"providerReady": true`, and
   `"profileWarning": null`. A typo in the profile name falls back to `dev`
   and says so in `profileWarning`.
3. **Prewarm** the eight prepared briefs into the service's own disk. This
   spends Qloo quota once per brief, and the model allowance if the gateway is
   on:

   ```bash
   python3 scripts/prewarm.py --base-url $HOST            # what is held (free)
   python3 scripts/prewarm.py --live --base-url $HOST     # fetch what is not
   ```

   It stops at the first rate limit. Any brief it reports as *"no direction
   was supported"* should be swapped for another in
   `shared/demoBriefs.json`, then redeployed and prewarmed. In judging,
   evidence is held for 14 days (`CULTUREFORGE_EVIDENCE_TTL_HOURS` overrides
   this). Rerun the prewarm if judging lasts longer.
4. **Smoke-test.** This is free:

   ```bash
   python3 scripts/smoke_test.py $HOST
   ```

5. **Click through** the [demo script](DEMO.md) once in a private window.

## During judging

- `GET $HOST/api/health` at any time shows the profile, calls made this
  hour and day, and the cache size. It never calls Qloo.
- Prepared briefs marked **Evidence held** cost nothing.

## If Qloo rate-limits the key

- What judges see: a stated message ("Qloo rate limited this key…"), never
  an empty panel. Live calls pause for `QLOO_RATE_LIMIT_COOLDOWN_SECONDS`
  (default 60) instead of retrying, and held evidence keeps working.
- If it persists, set `QLOO_LIVE_ENABLED=false` and restart. The service then
  serves held evidence only, so every prepared brief keeps working, and a
  new brief gets a stated "live retrieval is switched off" message.
- Do **not** switch back to `dev` to "protect quota" mid-judging. The dev
  budget would refuse calls on top of Qloo's own limit. The kill switch is
  the right lever.

## Rollback

| Problem | Do this |
| --- | --- |
| The new deploy is broken | In the host's dashboard, redeploy the previous successful deploy. The `/data` disk, and with it the held evidence, survives. |
| Spend is higher than expected | Set `RUN_PROFILE=dev` (budgets return: 20 Qloo calls an hour, 100 a day) or `QLOO_LIVE_ENABLED=false`, then restart. |
| The model misbehaves | Set `AI_GATEWAY_ENABLED=false`. Directions fall back to the rule composer, the agent card says the rules answer stands, and *Ask the evidence* returns a stated 503. |
| The disk is lost | Redeploy, then rerun the prewarm (step 3). |

## After judging

Set `RUN_PROFILE=dev` again, so a link that is still circulating cannot spend
an unbounded amount.
