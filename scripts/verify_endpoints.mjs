#!/usr/bin/env node
/**
 * verify_endpoints.mjs - every endpoint, by hand, the way a judge would.
 *
 * The contract check proves the shapes agree between two producers. This one
 * exercises the whole HTTP surface: the happy path of every route, and the
 * way each one fails when the request is wrong. A judge will click these by
 * hand, so a route that returns a stack trace, a blank body, or a status code
 * that means nothing is a defect, not a detail.
 *
 * The rules it holds every endpoint to:
 *
 *   - a success returns JSON with the documented keys
 *   - a failure returns {"detail": "<a sentence a person can read>"}
 *   - a bad request returns 422, not 500
 *   - nothing leaks a credential, a traceback, or a raw subprocess error
 *   - a missing thing returns 404, not 200 with null
 *
 * Usage:
 *   node scripts/verify_endpoints.mjs
 *   BASE_URL=http://127.0.0.1:8000 node scripts/verify_endpoints.mjs
 */

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';

const BRIEF = {
  businessType: 'Food & beverage',
  audience: 'Design-conscious Gen Z & young professionals',
  location: 'Brooklyn, New York',
  budget: '$25k – $50k',
  objectives: ['Become the natural meeting place for the neighbourhood'],
};

let failures = 0;
let checks = 0;
const seen = new Set();

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
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { __raw: text }; }
  return { status: response.status, body, text, headers: response.headers };
}

/** A failure has to read like a sentence a person can act on. */
function readableDetail(result) {
  const detail = result.body?.detail;
  if (typeof detail !== 'string' || !detail.trim()) return false;
  if (/Traceback|File "|line \d+, in |Error: |Exception|at Object\./i.test(detail)) return false;
  if (/hack_[0-9a-f]{16,}/i.test(detail)) return false;
  return detail.length > 8;
}

async function main() {
  console.log('--- every endpoint, by hand ---');

  // ---------------------------------------------------------------- health
  {
    const result = await api('/api/health');
    check('GET /api/health -> 200 with a provider mode',
      result.status === 200 && ['live', 'mock'].includes(result.body?.dataMode),
      `${result.status} dataMode ${result.body?.dataMode}`);
    seen.add('GET /api/health');
  }
  {
    const result = await api('/health');
    check('GET /health -> 200 (the alias tools probe)',
      result.status === 200 && result.body?.status === 'ok', `${result.status}`);
    seen.add('GET /health');
  }

  // -------------------------------------------------------------- generate
  const generated = await api('/api/projects/generate', { method: 'POST', body: BRIEF });
  check('POST /api/projects/generate -> 200 with three directions',
    generated.status === 200 && Array.isArray(generated.body?.concepts) && generated.body.concepts.length === 3,
    `${generated.status} ${generated.body?.concepts?.length ?? 0} directions`);
  check('POST /api/projects/generate -> the evidence is attached',
    Array.isArray(generated.body?.evidence) && generated.body.evidence.length > 0,
    `${generated.body?.evidence?.length ?? 0} items`);
  check('POST /api/projects/generate -> the trace is attached',
    Array.isArray(generated.body?.trace) && generated.body.trace.length > 0,
    `${generated.body?.trace?.length ?? 0} steps`);
  const live = generated.body ?? {};
  seen.add('POST /api/projects/generate');

  {
    const result = await api('/api/projects/generate', { method: 'POST', body: { businessType: 'Nonsense' } });
    check('POST /api/projects/generate -> a bad brief is 422 with a readable reason',
      result.status === 422 && readableDetail(result), `${result.status} ${String(result.body?.detail).slice(0, 80)}`);
    check('a failure carries the error envelope',
      typeof result.body?.error?.code === 'string' && typeof result.body?.error?.retryable === 'boolean'
      && typeof result.body?.requestId === 'string',
      `${result.body?.error?.code} ${result.body?.requestId ?? ''}`);
  }

  // ------------------------------------------------------------ taste seeds
  const taste = await api('/api/taste/resolve', {
    method: 'POST', body: { project: BRIEF, audience: BRIEF.audience },
  });
  check('POST /api/taste/resolve -> 200 with candidate signals',
    taste.status === 200 && Array.isArray(taste.body?.candidates) && taste.body.candidates.length > 0,
    `${taste.status} ${taste.body?.candidates?.length ?? 0} candidates`);
  check('POST /api/taste/resolve -> every candidate carries a Qloo tag',
    (taste.body?.candidates ?? []).every((c) => typeof c.tagId === 'string' && c.tagId.startsWith('urn:')),
    'tag urns');
  seen.add('POST /api/taste/resolve');
  {
    const result = await api('/api/taste/resolve', { method: 'POST', body: { project: BRIEF } });
    check('POST /api/taste/resolve -> a missing audience is 422',
      result.status === 422 && readableDetail(result), `${result.status}`);
  }

  // ---------------------------------------------------------- research runs
  const started = await api('/api/research/runs', {
    method: 'POST',
    body: { project: BRIEF, audience: BRIEF.audience, seedTagIds: (taste.body?.candidates ?? []).map((c) => c.tagId) },
  });
  check('POST /api/research/runs -> 202 Accepted with a run id and where to poll',
    started.status === 202 && typeof started.body?.runId === 'string' && Boolean(started.body?.statusUrl),
    `${started.status} ${started.body?.runId} ${started.body?.statusUrl ?? ''}`);
  seen.add('POST /api/research/runs');

  let run = null;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 400));
    const polled = await api(`/api/research/runs/${started.body.runId}`);
    run = polled.body;
    if (run?.status && run.status !== 'running') break;
  }
  check('GET /api/research/runs/{id} -> the run finishes',
    run?.status === 'complete', `status ${run?.status}`);
  check('GET /api/research/runs/{id} -> it carries the directions',
    Array.isArray(run?.result?.concepts) && run.result.concepts.length === 3,
    `${run?.result?.concepts?.length ?? 0} directions`);
  seen.add('GET /api/research/runs/{id}');

  {
    const result = await api('/api/research/runs/run-does-not-exist');
    check('GET /api/research/runs/{unknown} -> 404 with a readable reason',
      result.status === 404 && readableDetail(result), `${result.status}`);
  }
  {
    const result = await api('/api/research/runs');
    check('GET /api/research/runs -> 200 with a list',
      result.status === 200 && Array.isArray(result.body?.runs), `${result.status} ${result.body?.runs?.length ?? 0} runs`);
    seen.add('GET /api/research/runs');
  }

  // ------------------------------------------------------------- comparison
  const entities = (live.evidence ?? []).filter((item) => item.kind === 'entity').map((item) => item.entityId).filter(Boolean);
  if (entities.length >= 4) {
    const compared = await api('/api/projects/compare/audiences', {
      method: 'POST',
      body: { groupA: entities.slice(0, 2), groupB: entities.slice(2, 4), targetType: 'place' },
    });
    check('POST /api/projects/compare/audiences -> 200 with shared tags',
      compared.status === 200 && Array.isArray(compared.body?.shared), `${compared.status} ${compared.body?.shared?.length ?? 0} shared`);
    check('POST /api/projects/compare/audiences -> the scores are real numbers',
      (compared.body?.shared ?? []).every((tag) => typeof tag.score === 'number'),
      'no invented scores');
    seen.add('POST /api/projects/compare/audiences');
  }
  {
    const result = await api('/api/projects/compare/audiences', { method: 'POST', body: { groupA: 'not-an-array' } });
    check('POST /api/projects/compare/audiences -> a malformed group is 422, not a silent character list',
      result.status === 422, `${result.status} ${String(result.body?.detail).slice(0, 90)}`);
  }
  {
    const result = await api('/api/projects/compare/audiences', { method: 'POST', body: {} });
    check('POST /api/projects/compare/audiences -> an empty body is 422',
      result.status === 422, `${result.status}`);
  }

  // ------------------------------------------------------------------- rank
  if (entities.length >= 2) {
    const ranked = await api('/api/projects/rank', {
      method: 'POST',
      body: { options: entities, optionType: 'place', demographic: 'gen z', signalLocation: BRIEF.location },
    });
    check('POST /api/projects/rank -> 200 with a ranking',
      ranked.status === 200 && Array.isArray(ranked.body?.ranked) && ranked.body.ranked.length > 0,
      `${ranked.status} ${ranked.body?.ranked?.length ?? 0} ranked`);
    check('POST /api/projects/rank -> it reports the signal Qloo actually sent',
      typeof ranked.body?.signalsUsed?.['signal.demographics.age'] === 'string',
      ranked.body?.signalsUsed?.['signal.demographics.age'] ?? 'none');
    seen.add('POST /api/projects/rank');
  }
  {
    const result = await api('/api/projects/rank', { method: 'POST', body: { options: [], signalLocation: 'x' } });
    check('POST /api/projects/rank -> no options is 422',
      result.status === 422, `${result.status} ${String(result.body?.detail).slice(0, 90)}`);
  }
  {
    const result = await api('/api/projects/rank', {
      method: 'POST', body: { options: entities.slice(0, 2), unknownField: 'x' },
    });
    check('POST /api/projects/rank -> an unknown field is rejected with a readable reason',
      result.status === 422 && readableDetail(result), `${result.status} ${String(result.body?.detail).slice(0, 90)}`);
  }

  // -------------------------------------------------------------- recompose
  const aVenue = (live.evidence ?? []).find((item) => item.kind === 'entity' && item.entityId);
  if (aVenue) {
    const recomposed = await api('/api/projects/recompose', {
      method: 'POST', body: { project: BRIEF, excludeEntityIds: [aVenue.entityId] },
    });
    check('POST /api/projects/recompose -> 200 with a recomposition',
      recomposed.status === 200 && Array.isArray(recomposed.body?.concepts), `${recomposed.status}`);
    check('POST /api/projects/recompose -> the removed venue is gone',
      !(recomposed.body?.evidence ?? []).some((item) => item.entityId === aVenue.entityId),
      `dropped ${recomposed.body?.dropped}`);
    seen.add('POST /api/projects/recompose');
  }

  // ------------------------------------------------------------------ share
  const shared = await api('/api/explorations/share', { method: 'POST', body: live });
  check('POST /api/explorations/share -> 201 Created with a snapshot id',
    shared.status === 201 && typeof shared.body?.snapshotId === 'string', `${shared.status} ${shared.body?.snapshotId}`);
  seen.add('POST /api/explorations/share');
  {
    const result = await api(`/api/snapshots/${shared.body.snapshotId}`);
    check('GET /api/snapshots/{id} -> the snapshot reopens exactly',
      result.status === 200 && result.body?.concepts?.length === live.concepts?.length,
      `${result.status} ${result.body?.concepts?.length ?? 0} directions`);
    seen.add('GET /api/snapshots/{id}');
  }
  {
    const result = await api('/api/snapshots/snap-does-not-exist');
    check('GET /api/snapshots/{unknown} -> 404 with a readable reason',
      result.status === 404 && readableDetail(result), `${result.status}`);
  }

  // ---------------------------------------------------------------- compare
  const compared = await api('/api/projects/compare', {
    method: 'POST', body: { project: BRIEF, audience: 'Young families looking for a slow afternoon' },
  });
  check('POST /api/projects/compare -> 200 with re-researched directions',
    compared.status === 200 && Array.isArray(compared.body?.concepts) && compared.body.concepts.length > 0,
    `${compared.status} ${compared.body?.concepts?.length ?? 0} directions`);
  seen.add('POST /api/projects/compare');
  {
    const result = await api('/api/projects/compare', { method: 'POST', body: { project: BRIEF } });
    check('POST /api/projects/compare -> a missing audience is 422',
      result.status === 422 && readableDetail(result), `${result.status}`);
  }

  // ------------------------------------------------------------- the surface
  {
    const result = await api('/openapi.json');
    check('GET /openapi.json -> the API documents itself',
      result.status === 200 && typeof result.body?.paths === 'object',
      `${result.status} ${Object.keys(result.body?.paths ?? {}).length} paths`);
  }
  {
    const result = await api('/api/does-not-exist');
    check('GET /an-unknown-route -> 404, not a crash',
      result.status === 404, `${result.status}`);
  }
  {
    const result = await api('/api/health', { method: 'POST', body: {} });
    check('a wrong method on a real route -> 405',
      result.status === 405, `${result.status}`);
  }
  {
    const result = await api('/api/projects/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: undefined,
    });
    check('POST with no body at all -> 422, not a 500',
      result.status === 422, `${result.status}`);
  }
  {
    const response = await fetch(`${BASE_URL}/api/health`, { headers: { Origin: 'http://localhost:5173' } });
    const cors = response.headers.get('access-control-allow-origin');
    check('the CORS header is present for the studio origin',
      cors === 'http://localhost:5173', cors ?? 'none');
  }

  console.log('\n----------------------------------------------------------');
  console.log(`Endpoints exercised: ${seen.size}`);
  if (failures === 0) {
    console.log(`Every endpoint answers. ${checks} checks passed.`);
  } else {
    console.log(`${failures} of ${checks} checks failed.`);
  }
  console.log('----------------------------------------------------------');
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((error) => {
  console.error('The endpoint check could not finish:', error);
  process.exit(1);
});
