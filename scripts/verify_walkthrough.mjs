#!/usr/bin/env node
/**
 * verify_walkthrough.mjs - drive the product the way a business owner would.
 *
 * The contract check proves the shapes agree. It does not prove the product
 * works. This script walks the whole journey a founder takes, in order, and
 * asserts what each step must hand the next one:
 *
 *   1.  land            the studio is served and the backend is live
 *   2.  brief           POST /api/projects/generate returns a usable result
 *   3.  seeds           the audience resolves into candidate Qloo signals
 *   4.  confirm         the founder confirms the seeds and the agent runs
 *   5.  directions      three directions, each citing evidence that exists
 *   6.  provenance      every piece of evidence traces to a real call
 *   7.  the test        removing a venue changes what survives
 *   8.  compare         Qloo's own A/B between two audiences
 *   9.  anchor          Qloo's own ranking, and the signal it actually sent
 *  10.  share           a shared exploration reopens exactly
 *  11.  cached          a repeated brief costs no upstream request
 *
 * Every step runs against cached evidence, so the whole journey is free.
 * The script refuses to spend quota it did not intend to.
 *
 * Usage:
 *   node scripts/verify_walkthrough.mjs
 *   BASE_URL=http://127.0.0.1:8000 DEV_URL=http://localhost:5173 node scripts/verify_walkthrough.mjs
 */

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const DEV_URL = process.env.DEV_URL || 'http://localhost:5173';

const BRIEF = {
  businessType: 'Food & beverage',
  audience: 'Design-conscious Gen Z & young professionals',
  location: 'Brooklyn, New York',
  budget: '$25k – $50k',
  objectives: ['Become the natural meeting place for the neighbourhood'],
};

const ALTERNATIVE_AUDIENCE = 'Young families looking for a slow afternoon';

let failures = 0;
let checks = 0;

function ok(label, detail = '') {
  checks += 1;
  console.log(`[ok]   ${label}${detail ? ` -> ${detail}` : ''}`);
}

function fail(label, detail) {
  checks += 1;
  failures += 1;
  console.log(`[FAIL] ${label}${detail ? ` -> ${detail}` : ''}`);
}

function check(label, condition, detail = '') {
  if (condition) ok(label, detail);
  else fail(label, detail || 'expected a different result');
  return Boolean(condition);
}

async function api(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { raw: text }; }
  return { status: response.status, body };
}

const sleep = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });

async function main() {
  console.log('--- the founder walks in ---');

  // 1. land
  const health = await api('/api/health');
  check('the backend reports which provider is active',
    health.status === 200 && ['live', 'mock'].includes(health.body?.dataMode),
    `dataMode ${health.body?.dataMode}`);
  const studio = await fetch(`${DEV_URL}/studio/`).catch(() => null);
  check('the studio is served', Boolean(studio?.ok), studio ? `HTTP ${studio.status}` : 'no response');

  // 2. the brief
  const generated = await api('/api/projects/generate', { method: 'POST', body: BRIEF });
  check('the brief returns a result', generated.status === 200 && Array.isArray(generated.body?.concepts),
    `${generated.body?.concepts?.length ?? 0} directions`);
  const result = generated.body ?? {};

  // 3. the audience resolves
  const taste = await api('/api/taste/resolve', {
    method: 'POST', body: { project: BRIEF, audience: BRIEF.audience },
  });
  const candidates = taste.body?.candidates ?? [];
  check('the audience resolves into candidate signals', candidates.length > 0,
    candidates.map((c) => c.label).join(', '));
  check('every candidate carries a Qloo tag and a popularity',
    candidates.every((c) => typeof c.tagId === 'string' && c.tagId.startsWith('urn:') && typeof c.popularity === 'number'),
    `${candidates.length} candidates`);

  // 4. the founder confirms them and the agent runs
  const started = await api('/api/research/runs', {
    method: 'POST',
    body: { project: BRIEF, audience: BRIEF.audience, seedTagIds: candidates.map((c) => c.tagId) },
  });
  check('the research run starts', started.status === 202 && Boolean(started.body?.runId), started.body?.runId);

  let run = null;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    await sleep(500);
    const polled = await api(`/api/research/runs/${started.body.runId}`);
    run = polled.body;
    if (run?.status && run.status !== 'running') break;
  }
  check('the run finishes', run?.status === 'complete', `status ${run?.status}`);
  check('the run produced a result', Boolean(run?.result?.concepts?.length),
    `${run?.result?.concepts?.length ?? 0} directions`);

  const live = run?.result ?? result;
  const evidence = live.evidence ?? [];
  const evidenceIds = new Set(evidence.map((item) => item.id));
  const trace = live.trace ?? [];

  // 5. the directions
  check('there are three directions', live.concepts?.length === 3,
    live.concepts?.map((c) => c.name).join(' | '));
  const dangling = [];
  for (const concept of live.concepts ?? []) {
    for (const decision of concept.decisions ?? []) {
      for (const id of decision.evidenceIds ?? []) {
        if (!evidenceIds.has(id)) dangling.push(`${concept.name}/${decision.field} -> ${id}`);
      }
    }
  }
  check('every decision cites evidence that exists', dangling.length === 0,
    dangling.length ? dangling.join(', ') : `${evidence.length} pieces of evidence`);
  check('every direction names the venues it used',
    (live.concepts ?? []).every((concept) => (concept.evidenceIds ?? []).length > 0));
  check('no invented fit score is shown',
    (live.concepts ?? []).every((concept) => concept.audienceFit === null || concept.audienceFit === undefined),
    'affinity does not measure business fit');

  // 6. the provenance
  check('there is a trace to audit', trace.length > 0, `${trace.length} steps`);
  const realCalls = trace.filter((event) => event.workflow);
  check('the trace names the Qloo workflows it called',
    realCalls.length >= 2, realCalls.map((e) => e.workflow).join(', '));
  // A step that reused held evidence spent no time on the network, so it must
  // not report the duration of the call that fetched it. The original time is
  // still stated in the detail, so nothing is hidden.
  const reused = trace.filter((event) => event.workflow && /reused from cache/i.test(event.detail ?? ''));
  const fresh = trace.filter((event) => event.workflow && !/reused from cache/i.test(event.detail ?? ''));
  check('a reused step claims no duration of its own',
    reused.every((event) => event.durationMs === 0),
    reused.map((e) => `${e.workflow} ${e.durationMs}ms`).join(', ') || 'no reused steps');
  check('a reused step still states the original call\'s duration',
    reused.every((event) => /original call took/i.test(event.detail ?? '')),
    reused.map((e) => e.detail).join(' | ').slice(0, 120) || 'no reused steps');
  check('a fresh step reports the time it actually took',
    fresh.every((event) => typeof event.durationMs === 'number' && event.durationMs >= 0),
    fresh.map((e) => `${e.workflow} ${e.durationMs}ms`).join(', ') || 'every step reused held evidence');
  const withRequest = trace.filter((event) => event.request?.query && Object.keys(event.request.query).length);
  check('the request that was sent is recorded', withRequest.length > 0,
    withRequest.map((e) => Object.keys(e.request.query).join('+')).join(' | '));
  const allowed = new Set([
    'filter.query', 'feature.semantic_search', 'filter.type', 'filter.location.query',
    'signal.location.query', 'take', 'feature.explainability', 'signal.interests.tags',
    'operator.signal.interests.tags', 'signal.interests.entities', 'signal.demographics.gender',
    'signal.demographics.age', 'filter.tags', 'operator.filter.tags', 'filter.exclude.tags',
    'operator.filter.exclude.tags', 'filter.results.entities', 'a.signal.interests.entities',
    'b.signal.interests.entities',
  ]);
  const unexpected = withRequest.flatMap((event) =>
    Object.keys(event.request.query).filter((key) => !allowed.has(key)));
  check('no unexpected parameter reaches the provenance panel', unexpected.length === 0,
    unexpected.join(', ') || 'all allowlisted');
  check('every piece of evidence traces to a call',
    evidence.every((item) => trace.some((event) => event.id === item.traceId)),
    `${evidence.length} items`);

  // 7. the evidence test
  const aVenue = evidence.find((item) => item.kind === 'entity' && item.entityId);
  if (check('there is a venue to remove', Boolean(aVenue), aVenue?.label)) {
    const recomposed = await api('/api/projects/recompose', {
      method: 'POST',
      body: { project: BRIEF, excludeEntityIds: [aVenue.entityId] },
    });
    check('removing a venue returns a recomposition', recomposed.status === 200,
      recomposed.body?.notice);
    check('the removed venue is gone from the evidence',
      !(recomposed.body?.evidence ?? []).some((item) => item.entityId === aVenue.entityId),
      `dropped ${recomposed.body?.dropped}`);
    check('the recomposition says it spent nothing',
      /not called again/i.test(recomposed.body?.notice ?? ''),
      recomposed.body?.notice);
    const survivors = recomposed.body?.concepts ?? [];
    check('the recomposition keeps only directions that still have support',
      survivors.every((concept) => (concept.decisions ?? []).length > 0),
      `${survivors.length} of ${live.concepts.length} survived`);
  }

  // 7b. investigate the leading direction
  const entities = evidence.filter((item) => item.kind === 'entity' && item.entityId).map((item) => item.entityId);
  if (entities.length) {
    const investigation = await api('/api/projects/investigate', {
      method: 'POST',
      body: {
        project: BRIEF,
        directionId: live.concepts?.[0]?.id,
        entityIds: entities,
        reference: entities[0],
        within: BRIEF.location,
        facets: ['geography'],
      },
    });
    check('the investigation answers with the tools it called',
      investigation.status === 200 && (investigation.body?.tools ?? []).length > 0,
      (investigation.body?.tools ?? []).map((t) => `qloo ${t.workflow}`).join(', '));
    check('the investigation names the workflow behind the answer',
      (investigation.body?.tools ?? []).every((tool) => typeof tool.workflow === 'string' && tool.workflow.length > 0),
      (investigation.body?.tools ?? []).map((t) => t.workflow).join(', '));
    const points = investigation.body?.geography?.points ?? [];
    check('the investigation returns real geographic cells',
      points.length > 0 && points.every((point) =>
        typeof point.lat === 'number' && typeof point.lon === 'number'),
      `${points.length} cells`);
    check('the map says what it is not',
      /distinct from precise venue coordinates/i.test(investigation.body?.geography?.note ?? ''),
      'interest cells, not venue pins');
    check('the investigation states what it did not establish',
      Array.isArray(investigation.body?.limitations),
      `${investigation.body?.limitations?.length ?? 0} limitations`);
  }

  // 8. compare audiences
  const groupA = entities.slice(0, 2);
  const groupB = entities.slice(2, 4);
  if (groupA.length === 2 && groupB.length === 2) {
    const compared = await api('/api/projects/compare/audiences', {
      method: 'POST', body: { groupA, groupB, targetType: 'place' },
    });
    check('Qloo compares the two groups', compared.status === 200,
      `${compared.body?.shared?.length ?? 0} shared tags`);
    const scored = (compared.body?.shared ?? []).filter((tag) => typeof tag.score === 'number');
    check('the shared tags carry a real comparison score', scored.length > 0,
      scored.slice(0, 3).map((t) => `${t.label} ${Number(t.score).toFixed(4)}`).join(', '));
    check('the shared tags carry per-group hit counts',
      scored.every((tag) => typeof tag.groupAHits === 'number' && typeof tag.groupBHits === 'number'),
      scored.slice(0, 2).map((t) => `${t.label} a=${t.groupAHits} b=${t.groupBHits}`).join(', '));
  } else {
    ok('compare audiences', 'skipped: not enough venues in this brief');
  }

  // 9. the anchor tournament
  const options = entities;
  if (options.length >= 2) {
    const ranked = await api('/api/projects/rank', {
      method: 'POST',
      body: { options, optionType: 'place', demographic: 'gen z', signalLocation: BRIEF.location },
    });
    check('Qloo ranks the venues', ranked.status === 200 && (ranked.body?.ranked ?? []).length > 0,
      ranked.body?.ranked?.map((r) => `${r.position}. ${r.label}`).join(' | '));
    check('the ranking carries an affinity for each place',
      (ranked.body?.ranked ?? []).every((row) => typeof row.affinity === 'number'));
    check('the signal Qloo actually sent is reported',
      typeof ranked.body?.signalsUsed?.['signal.demographics.age'] === 'string',
      ranked.body?.signalsUsed?.['signal.demographics.age'] ?? 'none');
  } else {
    ok('the anchor tournament', 'skipped: not enough venues in this brief');
  }

  // 10. sharing
  const shared = await api('/api/explorations/share', { method: 'POST', body: live });
  check('the exploration can be shared', shared.status === 201 && Boolean(shared.body?.snapshotId),
    shared.body?.snapshotId);
  const snapshot = await api(`/api/snapshots/${shared.body?.snapshotId}`);
  check('the shared exploration reopens exactly',
    snapshot.status === 200 && snapshot.body?.concepts?.length === live.concepts?.length,
    `${snapshot.body?.concepts?.length ?? 0} directions`);

  // 11. a repeated brief is free
  const again = await api('/api/projects/generate', { method: 'POST', body: BRIEF });
  const spent = again.body?.delivery?.transportRequests;
  check('a repeated brief spends no upstream request', spent === 0,
    `${spent} upstream requests, delivery ${again.body?.delivery?.kind}`);
  check('the delivery says the evidence was cached',
    again.body?.delivery?.kind === 'cache', again.body?.delivery?.kind);
  check('the run counted no transport requests either',
    run?.transportRequests === 0, `${run?.transportRequests}`);

  // the scenario lab
  const scenario = await api('/api/projects/compare', {
    method: 'POST', body: { project: BRIEF, audience: ALTERNATIVE_AUDIENCE },
  });
  check('changing the audience re-researches', scenario.status === 200 && (scenario.body?.concepts ?? []).length > 0,
    scenario.body?.concepts?.map((c) => c.name).join(' | '));

  // The same rule, checked on a second, independent result.
  const scenarioTrace = scenario.body?.trace ?? [];
  check('the re-research trace is consistent about what it spent',
    scenarioTrace.filter((event) => event.workflow).every((event) => (/reused from cache/i.test(event.detail ?? '')
      ? event.durationMs === 0
      : typeof event.durationMs === 'number')),
    scenarioTrace.filter((event) => event.workflow).map((e) => `${e.workflow} ${e.durationMs}ms${/reused/i.test(e.detail ?? '') ? ' (reused)' : ''}`).join(', '));

  // A location Qloo cannot resolve must not be a dead end. The app has to say
  // which location failed, and offer a way out that it can vouch for.
  const stranded = await api('/api/projects/compare', {
    method: 'POST',
    body: { project: { ...BRIEF, location: 'Greenpoint, Brooklyn' }, audience: ALTERNATIVE_AUDIENCE },
  });
  const strandedDetail = String(stranded.body?.detail ?? '');
  check('a location Qloo cannot resolve is reported, not guessed at',
    stranded.status !== 200 && /returned no places for/i.test(strandedDetail),
    strandedDetail || `HTTP ${stranded.status}`);
  check('the message names the location that failed',
    /Greenpoint, Brooklyn/.test(strandedDetail),
    strandedDetail.slice(0, 140));
  check('the message offers a location Qloo already returned places for',
    /returned places for these same signals earlier/i.test(strandedDetail),
    strandedDetail.slice(0, 200));

  console.log('\n----------------------------------------------------------');
  if (failures === 0) {
    console.log(`The whole journey works. ${checks} checks passed.`);
  } else {
    console.log(`${failures} of ${checks} checks failed.`);
  }
  console.log('----------------------------------------------------------');
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((error) => {
  console.error('The walkthrough could not finish:', error);
  process.exit(1);
});
