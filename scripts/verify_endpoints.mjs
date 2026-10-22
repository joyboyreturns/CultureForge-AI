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
  check('POST /api/projects/generate -> 200 with one to three relevant directions',
    generated.status === 200 && Array.isArray(generated.body?.concepts) && generated.body.concepts.length >= 1 && generated.body.concepts.length <= 3,
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
  for (let attempt = 0; attempt < 225; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 400));
    const polled = await api(`/api/research/runs/${started.body.runId}`);
    run = polled.body;
    if (run?.status && run.status !== 'running') break;
  }
  check('GET /api/research/runs/{id} -> the run finishes',
    run?.status === 'complete', `status ${run?.status}`);
  check('GET /api/research/runs/{id} -> it carries the directions',
    Array.isArray(run?.result?.concepts) && run.result.concepts.length >= 1 && run.result.concepts.length <= 3,
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
  {
    const result = await api('/api/projects/challenge-probe', {
      method: 'POST', body: { project: BRIEF, directionId: 'direction-a', revision: { resolvedTags: 'not-a-list' } },
    });
    check('POST /api/projects/challenge-probe -> malformed probe evidence is 422 before any Qloo call',
      result.status === 422 && readableDetail(result), `${result.status} ${String(result.body?.detail).slice(0, 90)}`);
    seen.add('POST /api/projects/challenge-probe');
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

    // The evidence test: the part that can come back with a no.
    const tested = await api('/api/projects/challenge', { method: 'POST', body: { project: BRIEF } });
    check('POST /api/projects/challenge -> 200 with a verdict for every direction',
      tested.status === 200 && tested.body?.directions?.length > 0, `${tested.status}`);
    const verdicts = (tested.body?.directions ?? []).map((entry) => entry.verdict);
    check('POST /api/projects/challenge -> every verdict is one of the three',
      verdicts.every((verdict) => ['supported', 'contested', 'unproven'].includes(verdict)),
      verdicts.join(', '));
    check('POST /api/projects/challenge -> every verdict names its reason',
      (tested.body?.directions ?? []).every((entry) => typeof entry.reason === 'string' && entry.reason.length > 20),
      `${(tested.body?.directions ?? []).length} directions`);
    check('POST /api/projects/challenge -> it discloses what it judged on',
      /venues|places/i.test(tested.body?.directions?.[0]?.coverage?.note ?? ''),
      tested.body?.directions?.[0]?.coverage?.note?.slice(0, 60) ?? 'no coverage note');
    check('POST /api/projects/challenge -> the order it leaves them in is an order',
      Array.isArray(tested.body?.order) && tested.body.order.length === tested.body?.directions?.length,
      (tested.body?.order ?? []).join(', '));
    check('POST /api/projects/challenge -> the verdict says what it is about',
      typeof tested.body?.scope === 'string' && tested.body.scope.length > 3, tested.body?.scope);
    check('POST /api/projects/challenge -> the policy is recorded',
      typeof tested.body?.policyVersion === 'string' && tested.body.policyVersion.length > 3,
      tested.body?.policyVersion);
    check('POST /api/projects/challenge -> every direction states its claim and its falsifier',
      (tested.body?.directions ?? []).every((entry) => entry.claim && entry.falsifier && entry.unprovenIf),
      `${(tested.body?.directions ?? []).length} directions`);
    check('POST /api/projects/challenge -> every direction can be held to another place',
      (tested.body?.directions ?? []).every((entry) => (entry.alternatives ?? []).length > 0),
      `${(tested.body?.directions ?? []).length} directions`);

    // The lever: the same claim, held to a different place, answers differently.
    const anchor = (tested.body?.directions ?? [])[0]?.alternatives?.[0]?.entityId;
    if (anchor) {
      const reanchored = await api('/api/projects/challenge', {
        method: 'POST', body: { project: BRIEF, anchorEntityId: anchor },
      });
      check('POST /api/projects/challenge -> a direction can be held to a different place',
        reanchored.status === 200 && reanchored.body?.directions?.[0]?.anchor?.entityId === anchor,
        reanchored.body?.directions?.[0]?.anchor?.label ?? 'no anchor');
    }
    seen.add('POST /api/projects/challenge');
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

  // ------------------------------------------- Qloo's own workflow surface
  // Each of the five workflows the app can reach, called directly.
  const workflows = [
    {
      name: 'describe', path: '/api/qloo/describe',
      body: { entity: 'Union Square Park', entityType: 'place' },
      expect: (body) => body.workflow === 'describe' && body.resultCount >= 1,
    },
    {
      name: 'entity_tags', path: '/api/qloo/entity-tags',
      body: { entities: ['Union Square Park'], entityType: 'place' },
      expect: (body) => body.workflow === 'entity_tags' && Array.isArray(body.results),
    },
    {
      name: 'where_popular', path: '/api/qloo/where-popular',
      body: { entity: 'Starbucks', entityType: 'brand', within: 'United States' },
      expect: (body) => body.workflow === 'where_popular' && Array.isArray(body.points),
    },
    {
      name: 'audience_demographics', path: '/api/qloo/audience-demographics',
      body: { entity: 'Starbucks', entityType: 'brand' },
      expect: (body) => body.workflow === 'audience_demographics',
    },
  ];
  for (const workflow of workflows) {
    const result = await api(workflow.path, { method: 'POST', body: workflow.body });
    check(`POST ${workflow.path} -> answers in its own shape`,
      result.status === 200 && workflow.expect(result.body ?? {}),
      `${result.status} ${result.body?.error?.code ?? `${result.body?.resultCount ?? 0} results`}`);
    seen.add(`POST ${workflow.path}`);
  }
  {
    const result = await api('/api/qloo/describe', { method: 'POST', body: {} });
    check('POST /api/qloo/describe -> no entity is 422',
      result.status === 422 && readableDetail(result), `${result.status}`);
  }
  {
    const result = await api('/api/qloo/where-popular', { method: 'POST', body: { entity: 'Starbucks' } });
    check('POST /api/qloo/where-popular -> no area is 422',
      result.status === 422 && readableDetail(result), `${result.status}`);
  }

  // ---------------------------------------------------- the investigation loop
  {
    const facets = await api('/api/facets');
    check('GET /api/facets -> the questions an investigation can open',
      facets.status === 200 && Array.isArray(facets.body?.facets) && facets.body.facets.length > 0,
      `${facets.status} ${facets.body?.facets?.length ?? 0} facets`);
    seen.add('GET /api/facets');
  }
  if (entities.length) {
    const investigation = await api('/api/projects/investigate', {
      method: 'POST',
      body: {
        project: BRIEF,
        directionId: live.concepts?.[0]?.id,
        entityIds: entities,
        reference: entities[0],
        within: 'United States',
        facets: ['geography'],
      },
    });
    check('POST /api/projects/investigate -> answers with the tools it used',
      investigation.status === 200 && Array.isArray(investigation.body?.tools) && investigation.body.tools.length > 0,
      `${investigation.status} ${investigation.body?.tools?.length ?? 0} tools`);
    check('POST /api/projects/investigate -> it names the workflow it called',
      (investigation.body?.tools ?? []).every((tool) => typeof tool.workflow === 'string'),
      (investigation.body?.tools ?? []).map((t) => t.workflow).join(', '));
    check('POST /api/projects/investigate -> it states what it did not establish',
      Array.isArray(investigation.body?.limitations),
      `${investigation.body?.limitations?.length ?? 0} limitations`);
    seen.add('POST /api/projects/investigate');
  }
  {
    const result = await api('/api/projects/investigate', {
      method: 'POST', body: { project: BRIEF, entityIds: [], facets: [] },
    });
    check('POST /api/projects/investigate -> nothing to investigate is 422',
      result.status === 422 && readableDetail(result), `${result.status}`);
  }

  // ------------------------------------------------------ the platform layer
  {
    const created = await api('/api/workspaces', { method: 'POST', body: { name: 'Endpoint Audit Co' } });
    check('POST /api/workspaces -> 201 with a workspace',
      created.status === 201 && typeof created.body?.id === 'string', `${created.status} ${created.body?.id}`);
    seen.add('POST /api/workspaces');

    const key = await api(`/api/workspaces/${created.body.id}/keys`, {
      method: 'POST', body: { scopes: ['read', 'export'] },
    });
    check('POST /api/workspaces/{id}/keys -> 201 with a key shown once',
      key.status === 201 && typeof key.body?.key === 'string' && key.body.key.startsWith(key.body.prefix),
      `${key.status} ${key.body?.prefix}`);
    const listed = await api(`/api/workspaces/${created.body.id}/keys`);
    check('GET /api/workspaces/{id}/keys -> the secret is not stored in the clear',
      listed.status === 200 && !JSON.stringify(listed.body).includes(key.body.key),
      `${listed.status}`);
    seen.add('GET /api/workspaces/{id}/keys');

    const authenticated = await fetch(`${BASE_URL}/api/explorations`, {
      headers: { Authorization: `Bearer ${key.body.key}` },
    });
    check('a bearer key authenticates -> 200', authenticated.status === 200, `${authenticated.status}`);

    const bad = await fetch(`${BASE_URL}/api/explorations`, {
      headers: { Authorization: 'Bearer cfk_nope.nope' },
    });
    check('a wrong key is rejected -> 401', bad.status === 401, `${bad.status}`);

    const revoked = await api(`/api/workspaces/${created.body.id}/keys/${key.body.id}`, { method: 'DELETE' });
    check('DELETE a key -> 204, and it stops working', revoked.status === 204, `${revoked.status}`);
    const after = await fetch(`${BASE_URL}/api/explorations`, {
      headers: { Authorization: `Bearer ${key.body.key}` },
    });
    check('a revoked key no longer authenticates -> 401', after.status === 401, `${after.status}`);
    seen.add('DELETE /api/workspaces/{id}/keys/{keyId}');
  }
  {
    const usage = await api('/api/usage');
    check('GET /api/usage -> the requests it has served',
      usage.status === 200 && typeof usage.body?.requests === 'number' && usage.body.requests > 0,
      `${usage.status} ${usage.body?.requests} requests, ${usage.body?.upstreamCalls} upstream`);
    seen.add('GET /api/usage');
  }
  {
    const list = await api('/api/explorations');
    check('GET /api/explorations -> the saved explorations',
      list.status === 200 && Array.isArray(list.body?.explorations) && list.body.explorations.length > 0,
      `${list.status} ${list.body?.explorations?.length ?? 0} saved`);
    seen.add('GET /api/explorations');

    const id = list.body.explorations[0].id;
    const one = await api(`/api/explorations/${id}`);
    check('GET /api/explorations/{id} -> one saved exploration, with its result',
      one.status === 200 && one.body?.id === id && Boolean(one.body?.result),
      `${one.status}`);
    seen.add('GET /api/explorations/{id}');

    const markdown = await fetch(`${BASE_URL}/api/explorations/${id}/export?format=markdown`);
    const text = await markdown.text();
    check('GET /api/explorations/{id}/export -> Markdown a founder could send',
      markdown.status === 200 && text.includes('#') && text.length > 200,
      `${markdown.status} ${text.length} chars`);
    const asJson = await fetch(`${BASE_URL}/api/explorations/${id}/export?format=json`);
    check('GET /api/explorations/{id}/export -> JSON with a download name',
      asJson.status === 200 && (asJson.headers.get('content-disposition') ?? '').includes('.json'),
      `${asJson.status}`);
    const badFormat = await fetch(`${BASE_URL}/api/explorations/${id}/export?format=pdf`);
    check('GET /api/explorations/{id}/export -> an unknown format is 422',
      badFormat.status === 422, `${badFormat.status}`);
    seen.add('GET /api/explorations/{id}/export');
  }
  {
    const result = await api('/api/explorations/exp-does-not-exist');
    check('GET /api/explorations/{unknown} -> 404',
      result.status === 404 && readableDetail(result), `${result.status}`);
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
