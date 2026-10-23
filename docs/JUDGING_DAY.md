# Judging-day runbook

Everything here uses the deployed service from [DEPLOY.md](DEPLOY.md). Replace
`$HOST` with its HTTPS URL.

## Before judging opens

1. **Check the profile.** On your Ubuntu server set `RUN_PROFILE=judging` in
   `.env` (keep `QLOO_LIVE_ENABLED=true`) and run
   `docker compose up -d --force-recreate`. (The Render blueprint already
   deploys with it.) No code change is needed.
2. **Check health.**

   ```bash
   curl -s $HOST/api/health
   ```

   You should see `"profile": "judging"`, every limit under `budgets`
   reported as `"unlimited"`, `"providerReady": true`, and
   `"profileWarning": null`. A typo in the profile name falls back to `dev`
   and says so in `profileWarning`.
3. **Prewarm** selected prepared briefs into the service's own disk. This
   spends Qloo quota once per brief, and the model allowance if the gateway is
   on:

   ```bash
   python3 scripts/prewarm.py --base-url $HOST            # what is held (free)
   python3 scripts/prewarm.py --live --only tokyo-morning-bakery --base-url $HOST  # deliberate bounded first example
   ```

   It rests 20 seconds between briefs (`--pause`), and if Qloo rate-limits it
   waits out the stated pause once and tries that step again; a second limit
   stops the run. A brief costs about nine Qloo workflows and Qloo's own limit
   is unpublished (see [LIMITATIONS.md](LIMITATIONS.md)), so expect to prewarm
   a few briefs per hour rather than all nine at once. Start days early,
   and rerun it with `--skip-held` to leave alone the briefs whose evidence is
   already held (their evidence test may still be cold, so run without it
   once at the end). Any brief it reports as *"no direction
   was supported"* should be swapped for another in
   `shared/demoBriefs.json`, then redeployed and prewarmed. In judging,
   evidence is held for 30 days (`CULTUREFORGE_EVIDENCE_TTL_HOURS` overrides
   this). Rerun the prewarm if judging lasts longer.
4. **Smoke-test.** This is free:

   ```bash
   python3 scripts/smoke_test.py $HOST
   ```

5. **Click through** the [demo script](DEMO.md) once in a private window.

## Before judging: heal the agent reports of the prepared demos

Qloo evidence is shipped in `shared/demoPack.json`; the agent's analysis is not, because it is the model's
output for one particular run. The first visitor to a prepared demo therefore triggers its agent loop
(about ten model requests, one to two minutes) unless it was run before. Open each of the three featured
demos once from your own browser, or run `python3 scripts/brief_probe.py --base-url $HOST --example
tokyo-morning-bakery` (and `paris-ice-cream`, `melbourne-specialty-coffee`), and wait for
`AGENT mode=frontier_ai`. Check `--challenge` too if you want its verdicts held. A report that ended
because Qloo was switched off or rate-limited is **never held** (it used to be, and the demos then
showed one failed step), and an older one is discarded on the next open.

## During judging

- **Fair use.** `GET $HOST/api/health` shows `admission.coldRunsActive` against `maxColdRuns`. A visitor
  who starts more than eight new ideas in an hour, or a ninth idea while three are being researched, gets a
  stated 429 and the prepared examples keep opening. Raise `CULTUREFORGE_COLD_RUNS_PER_CLIENT_HOUR` in
  `.env` only if a judge reports being refused, and recreate the container.

- `GET $HOST/api/health` at any time shows the profile, calls made this
  hour and day, and the cache size. It never calls Qloo.
- Prepared briefs marked **Evidence held** cost nothing.

## If Qloo rate-limits the key

- What judges see: a stated message ("Qloo rate limited this key…"), never
  an empty panel. Live calls pause for `QLOO_RATE_LIMIT_COOLDOWN_SECONDS`
  (default 60) instead of retrying, and held evidence keeps working.
- If it persists, set `QLOO_LIVE_ENABLED=false` in `.env` and recreate the
  container. The service then
  serves held evidence only, so every prepared brief keeps working, and a
  new brief gets a stated "live retrieval is switched off" message.
- Do **not** switch back to `dev` to "protect quota" mid-judging. The dev
  budget would refuse calls on top of Qloo's own limit. The kill switch is
  the right lever.

## Rollback

| Problem | Do this |
| --- | --- |
| The new deploy is broken | `git checkout <previous-commit> && docker compose up -d --build`. (On Render, redeploy the previous deploy.) The `/data` volume, and with it the held evidence, survives. |
| Spend is higher than expected | Set `RUN_PROFILE=dev` (budgets return: 20 Qloo calls an hour, 100 a day) or `QLOO_LIVE_ENABLED=false` in `.env`, then `docker compose up -d --force-recreate`. |
| The model misbehaves | Set `AI_GATEWAY_ENABLED=false` in `.env` and recreate the container. Directions fall back to the rule composer, the agent card says the rules answer stands, and *Ask the evidence* returns a stated 503. |
| The volume is lost, or the machine was rebuilt | Start it again, then rerun the prewarm (step 3). Restore `data.tgz` first if you took a backup. |
| Power cut or reboot | The container restarts with Docker. Check `docker compose ps`, then run the smoke test. |

## After judging

Set `RUN_PROFILE=dev` again, so a link that is still circulating cannot spend
an unbounded amount.

## The three shipped demos (added 22 Oct 2026)

`shared/demoPack.json` ships real Qloo answers for three briefs, with their original acquisition times, plus the
verified venue geocodes. `backend/demo_pack.py` places them in the evidence store at start-up as pinned entries
(they do not expire), so a fresh clone, or a server with `QLOO_LIVE_ENABLED=false`, opens them with no Qloo request:

1. **Artisan bakery for morning commuters, Tokyo** (9 of 10 venues on the map, 20 interest cells)
2. **Ice cream parlour, Paris** (5 of 9 on the map; the rest were returned for other cities and are not plotted)
3. **Specialty coffee shop, Melbourne** (9 of 10 on the map, 20 interest cells)

Rebuild the pack (reads held evidence; `--live` fetches any gap once; `--allow-gaps` writes what is held):

```bash
python3 scripts/export_demo_pack.py --live --allow-gaps
```

What is not in the pack: model-written direction names and the optional agent analysis (they run per server, within
the model budget), and venue geocodes for any brief other than the three.

## When a judge types their own brief

| Input | What happens |
| --- | --- |
| A known business ("flower shop", "pizza", "gym") | Resolved from a category table, then to Qloo's own place category tag |
| An unfamiliar one ("bubble tea shop") | Looked up in Qloo's taxonomy; a place counts only if its text matches the distinctive word |
| Two businesses ("bakery and bookstore") or no business | Asks the founder to name one; nothing is guessed |
| A city Qloo will not search ("Narnia") | "Use a city and country" with a way back to the brief |
| A category with places but no audience overlap in that city | One extra request for the category's places without the audience tags, stated in the answer |
| Real references but no cultural signature that fits a recipe | One narrow "Local Reference Study" direction, labelled promising but unverified |
| Qloo timeout or rate limit | A stated, retryable failure; held evidence still opens |

Live checks on 22 Oct 2026: bubble tea in Los Angeles returned 9 direct businesses (it returned none before the
place-category fix); Narnia gave the friendly location message; vegan restaurant in Berlin timed out at Qloo
(a heavy category filter) and is reported as a retryable failure, not as an answer.
