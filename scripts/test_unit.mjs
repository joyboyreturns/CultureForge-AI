/** Regression checks for portable evidence records; no browser or API needed. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';

async function loadTs(path, replacements = {}) {
  let source = readFileSync(new URL(path, import.meta.url), 'utf8');
  for (const [from, to] of Object.entries(replacements)) source = source.replace(from, to);
  const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } });
  const url = `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`;
  return { module: await import(url), url };
}
const summary = await loadTs('../src/evidenceSummary.ts');
const intentView = (await loadTs('../src/intentView.ts')).module;
const intentViewUrl = (await loadTs('../src/intentView.ts')).url;
const { renderBrief } = (await loadTs('../src/brief.ts', { "'./evidenceSummary'": `'${summary.url}'`, "'./intentView'": `'${intentViewUrl}'` })).module;
const concept = { id: 'direction', name: 'A proposed experience', tagline: 'A hypothesis', description: 'A cultural interpretation', investment: '$25k',
  signals: [], limitations: ['No demand evidence'], evidenceIds: ['known', 'missing'], decisions: [
    { field: 'format', proposal: 'Try a quiet setting', ruleId: 'quiet', evidenceIds: ['known'] },
    { field: 'location', proposal: 'An unverified source', ruleId: 'location', evidenceIds: ['missing'] },
  ] };
const evidence = [{ id: 'known', label: 'Original source', entityId: 'qloo-id', kind: 'entity' }];
assert.equal(summary.module.citationCoverage(concept, evidence).numerator, 1, 'Missing source IDs cannot count as covered');
assert.equal(summary.module.citationCoverage(concept, []).numerator, 0, 'Removing the last source must remove citation coverage');
const result = { projectId: 'project', project: { audience: 'Founders', location: 'Brooklyn', budget: '$25k', objectives: [] },
  delivery: { kind: 'cache', transportRequests: 0 }, evidence, trace: [], notice: 'Bounded sample' };
const challenge = { policyVersion: 'test-policy', directions: [{ directionId: 'direction', verdict: 'unproven', scope: 'Sample only',
  reason: 'One check is missing', claim: 'A claim', falsifier: 'Contradiction', unprovenIf: 'Missing check',
  anchor: { label: 'Alternative place' }, originalAnchor: { label: 'Original source' }, isCounterfactual: true,
  checks: [{ name: 'Culture', result: 'mixed', detail: 'No qualifying evidence' }] }] };
const record = renderBrief(result, [concept], challenge);
assert.match(record, /Alternative place/);
assert.match(record, /original reference: Original source\. The concept was not recomposed/);
assert.match(record, /unavailable in this evidence set; do not treat as verified/);
assert.match(record, /New upstream requests for this delivery: 0/);
assert.match(record, /Verdict: unproven/);
assert.match(record, /No demand evidence/);
assert.doesNotMatch(renderBrief(result, [concept]), /Verdict: supported/);
console.log('[ok] Citation coverage rejects missing sources; export preserves zero-cost delivery, uncertainty and counterfactual anchors.');

const { module: notebook } = await loadTs('../src/decisionNotebook.ts');
const { module: dependence } = await loadTs('../src/evidenceDependence.ts');
const keyedResult = { ...result, concepts: [concept] };
assert.notEqual(notebook.notebookKey(keyedResult, concept), notebook.notebookKey({ ...keyedResult, evidence: [] }, concept), 'Field notes cannot silently follow a different evidence set');
assert.notEqual(notebook.notebookKey(keyedResult, concept), notebook.notebookKey(keyedResult, { ...concept, description: 'A revised hypothesis' }), 'Field notes must belong to the same proposal');
assert.equal(notebook.defaultDecision(keyedResult, concept).observations, '', 'A new notebook cannot contain invented field results');
assert.match(notebook.renderDecision(notebook.defaultDecision(keyedResult, concept)), /not Qloo evidence/);
assert.match(notebook.renderDecision(notebook.defaultDecision(keyedResult, concept)), /field validation has not been demonstrated/);
const experiment = { ...notebook.defaultDecision(keyedResult, concept), owner: 'Strategy lead', reviewDate: '2026-11-06', spendingCap: 'USD 200' };
const experimentRecord = notebook.renderDecision(experiment);
assert.match(experimentRecord, /Accountable owner: Strategy lead/);
assert.match(experimentRecord, /Review date: 2026-11-06/);
assert.match(experimentRecord, /team-entered, not a cost estimate\): USD 200/);
const browserStorage = new Map();
globalThis.localStorage = { getItem: (key) => browserStorage.get(key) ?? null };
browserStorage.set('legacy', JSON.stringify(notebook.defaultDecision(keyedResult, concept)));
browserStorage.set('experiment', JSON.stringify(experiment));
browserStorage.set('corrupt', JSON.stringify({ ...experiment, owner: { name: 'Invalid shape' } }));
assert.ok(notebook.readDecision('legacy'), 'Existing notes remain readable without the new optional fields');
assert.equal(notebook.readDecision('experiment').reviewDate, '2026-11-06');
assert.equal(notebook.readDecision('corrupt'), null, 'Malformed optional fields cannot crash the notebook export');
delete globalThis.localStorage;
const original = { ...concept, signals: [], image: '', imageAlt: '', evidenceIds: ['known'] };
const changed = { ...original, description: 'Rebuilt around another place', evidenceIds: ['other'] };
const replacement = [{ id: 'other', entityId: 'other-qloo-id', kind: 'entity' }];
assert.equal(dependence.compareDirection(original, { concepts: [changed], evidence: replacement }, evidence), 'changed', 'A source change must not conceal a changed answer');
assert.equal(dependence.compareDirection(original, { concepts: [{ ...original, name: 'Rule name', tagline: 'Rule tagline' }], evidence }, evidence), 'unchanged', 'Omitting optional model naming is not evidence dependence');
assert.equal(dependence.compareDirection(original, { concepts: [{ ...original, evidenceIds: ['other'] }], evidence: replacement }, evidence), 'sources');
assert.equal(dependence.compareDirection(original, { concepts: [], evidence: [] }, evidence), 'disappeared');
console.log('[ok] Notebook notes stay attached to their proposal and evidence; removal reports answer changes separately from source-only changes.');

const { module: tour } = await loadTs('../src/tourSteps.ts');
assert.equal(tour.tourNeedsEvidence(1), false);
assert.equal(tour.tourNeedsEvidence(2), true);
assert.equal(tour.TOUR_STEPS.length, 7);
assert.ok(tour.TOUR_STEPS.some((step) => step.id === "difference" && tour.tourNeedsEvidence(tour.TOUR_STEPS.indexOf(step))), "the Qloo-contribution step needs real evidence");
console.log('[ok] Guided tour supports the brief before evidence exists and requires real evidence for the remaining interactions.');

const { module: initialResearch } = await loadTs('../src/initialResearch.ts');
const preview = { status: 'running', partialResult: { evidence: [{ id: 'real-source' }], concepts: [] } };
assert.equal(initialResearch.shouldOpenInitial(preview, true, false), true, 'Evidence is useful even before a direction exists');
assert.equal(initialResearch.shouldOpenInitial(preview, true, true), false, 'Watching the trace must not redirect back to the preview');
assert.equal(initialResearch.shouldOpenInitial(preview, false, false), false);
assert.equal(initialResearch.shouldOpenInitial({ ...preview, partialResult: null }, true, false), false);
assert.equal(initialResearch.shouldOpenInitial({ ...preview, partialResult: { evidence: [] } }, true, false), false);
for (const status of ['complete', 'failed', 'clarify']) assert.equal(initialResearch.shouldOpenInitial({ ...preview, status }, true, false), false, 'Terminal states retain their own result or recovery path');
const initialBrief = { businessType: 'Food & beverage', businessIdea: 'Vegan restaurant', audience: 'Plant-based diners', location: 'London', budget: '$25k', objectives: ['Community', 'Distinctive'] };
const initialAnswer = { projectId: 'preview', project: initialBrief };
const fullAnswer = { projectId: 'finished', project: { ...initialBrief, objectives: ['Distinctive', 'Community'] } };
assert.equal(initialResearch.shouldUpgradeInitial(initialAnswer, fullAnswer, 'preview', true), true);
assert.equal(initialResearch.shouldUpgradeInitial(initialAnswer, fullAnswer, 'preview', false), false, 'Completion must not navigate away from another screen');
assert.equal(initialResearch.shouldUpgradeInitial(initialAnswer, fullAnswer, 'other', true), false, 'Another exploration must not be replaced');
assert.equal(initialResearch.shouldUpgradeInitial(initialAnswer, { ...fullAnswer, project: { ...initialBrief, location: 'Berlin' } }, 'preview', true), false, 'Completion from a different brief must not replace this preview');
assert.equal(initialResearch.shouldUpgradeInitial(null, fullAnswer, 'preview', true), false);
console.log('[ok] Initial evidence opens once while research is running, including evidence without directions; terminal states and explicit trace viewing are preserved.');

const { module: map } = await loadTs('../src/components/map/mapModel.ts');
const place = (id, cls, extra = {}) => ({ id, kind: 'entity', label: id, entityId: `qloo-${id}`, relevance: cls ? { evidenceClass: cls, relationship: 'direct', category: 'bakery', anchorEligible: true, geography: '', audience: '', confidence: 'high', reasons: [] } : null, ...extra });
const venues = [place('direct', 'direct_business', { address: '1-2 Ginza' }), place('fan', 'audience_affinity', { address: 'x' }),
  place('unconfirmed', 'unverified_geography', { address: 'Somewhere 3' }), place('bare', 'indirect_business'), place('none', null, { address: 'y' }),
  { id: 'seed', kind: 'tag', label: 'Seed' }];
const candidates = map.venueCandidates(venues);
assert.equal(candidates.length, 5, 'Only returned places are venue candidates');
assert.deepEqual(candidates.filter((c) => c.eligible).map((c) => c.venue.id), ['direct', 'unconfirmed', 'bare']);
assert.equal(map.placementOf(candidates[1], undefined).state, 'not_plotted', 'An audience-affinity place is never drawn as a venue');
assert.equal(map.placementOf(candidates[0], undefined).state, 'pending', 'A venue is not drawn before the geocode answers');
assert.equal(map.placementOf(candidates[3], undefined).state, 'not_plotted', 'A venue with no address is listed, not guessed');
assert.equal(map.placementOf(candidates[2], { id: 'unconfirmed', status: 'outside_city', reason: 'Outside Tokyo' }).state, 'not_plotted', 'An address outside the city is not plotted');
const plottedAt = map.placementOf(candidates[0], { id: 'direct', status: 'plotted', lat: 35.67, lon: 139.76, source: 'Nominatim', precision: 'address match' });
assert.equal(plottedAt.state, 'plotted');
assert.equal(map.normaliseGeocode({ id: 'a', status: 'plotted' }).status, 'not_found', 'A plotted answer without coordinates is not plotted');
assert.equal(map.normaliseGeocode({ id: 'a', status: 'made-up' }).status, 'unavailable');
assert.equal(map.isDefinitive({ id: 'a', status: 'unavailable' }), false, 'A transport failure is never held as an answer');
const many = Array.from({ length: 13 }, (_, i) => ({ venue: place(`v${i}`, 'direct_business', { address: `${i} Main St` }), eligible: true }));
const batches = map.geocodeBatches(many, 'Tokyo, Japan', (id) => id === 'v0');
assert.deepEqual(batches.map((b) => b.length), [3, 3, 3, 3], 'Held answers are not requested again, and a batch stays small so an abandoned request loses little');
assert.equal(batches[0][0].city, 'Tokyo, Japan');
const view = map.decodeMapHash(map.encodeMapHash({ lat: 35.6812, lon: 139.7671, zoom: 13.5 }));
assert.deepEqual(view, { lat: 35.6812, lon: 139.7671, zoom: 13.5 });
assert.equal(map.decodeMapHash('#map=95,0,3'), null);
assert.equal(map.decodeMapHash('#workspace/create'), null);
const newYork = { west: -74.05, south: 40.6, east: -73.9, north: 40.8 };
assert.equal(map.nearBounds({ lat: 35.68, lon: 139.76 }, newYork), false, 'A shared Tokyo view is never restored over New York evidence');
assert.equal(map.nearBounds({ lat: 40.7, lon: -73.95 }, newYork), true);
assert.equal(map.nearBounds({ lat: 40.7, lon: -73.95 }, null), false, 'With no placed evidence, no shared view can be verified');
const targets = [{ kind: 'area', id: 'area', label: 'Brooklyn, New York — all evidence' }, { kind: 'venue', id: 'v', label: 'Devoción' }];
assert.equal(map.matchSearch('Tokyo', targets), null, 'Search never invents a city the data does not hold');
assert.equal(map.matchSearch('devo', targets).id, 'v');
const features = map.venueFeatures([{ venue: venues[0], kind: 'direct', at: { lat: 1, lon: 2 } }, { venue: venues[2], kind: 'direct', at: { lat: 1.1, lon: 2 } }], new Set(['direct']), true);
assert.deepEqual(features.features.map((f) => [f.properties.cited, f.properties.dim]), [[1, 0], [0, 1]], 'A chosen direction lights its venues and dims the rest');
assert.equal(map.cellMetric([{ lat: 0, lon: 0, affinity: 0.9, popularity: 0.1 }, { lat: 1, lon: 1, affinity: 0.901, popularity: 0.5 }]).name, 'popularity', 'A flat affinity is not drawn as a comparison');
assert.ok(map.uncertainties(venues[0], plottedAt).some((u) => /not a surveyed venue point/.test(u)));
const { url: layersUrl } = await loadTs('../src/components/map/layers.ts');
const { module: mapStyle } = await loadTs('../src/components/map/style.ts', { "'./layers'": `'${layersUrl}'` });
const empty = { type: 'FeatureCollection', features: [] };
const styleArgs = { theme: 'dark', colors: {}, data: { cells: empty, venues: empty, context: empty, selected: empty }, visible: { heat: true, venues: true, context: true }, bounds: null };
const streets = mapStyle.composeStyle({ ...styleArgs, mode: 'streets' });
assert.equal(streets.sources.openmaptiles.url, 'https://tiles.openfreemap.org/planet');
assert.equal(streets.sources.venues.cluster, true, 'Venues are clustered');
const grid = mapStyle.composeStyle({ ...styleArgs, mode: 'grid' });
assert.equal(grid.sources.openmaptiles, undefined, 'The fallback loads no tiles');
assert.equal(grid.glyphs, undefined);
assert.ok(!grid.layers.some((l) => l.type === 'symbol'), 'The fallback needs no glyphs');
console.log('[ok] The map plots only geocoded venues, never restores another city, searches only held evidence, and falls back without tiles.');

const entry = (state, extra = {}) => ({ role: 'primary', phrase: 'bakery', categoryLabel: 'Bakery', state, queriesTried: ['bakery'], tag: null,
  placeCount: 2, directCount: 1, places: [], modifiers: [], categoryOnly: false, message: '', ...extra });
const comp = (phrase, modifiers = []) => ({ role: 'primary', phrase, categoryId: '', categoryLabel: phrase, status: 'canonical', queries: [phrase], modifiers, source: 'rules' });
const plain = { original: 'Bakery', components: [comp('bakery')], hybrid: false, ambiguous: false, clarification: '', unused: [], substitutions: [], source: 'rules', evidence: [entry('exact')], overlap: null };
assert.equal(intentView.intentIsWorthShowing(plain), false, 'An exact, unspecialised, single-business reading adds nothing to show');
assert.equal(intentView.intentIsWorthShowing({ ...plain, hybrid: true }), true);
assert.equal(intentView.intentIsWorthShowing({ ...plain, components: [comp('vegan restaurant', ['vegan'])] }), true, 'A specialisation is always shown');
assert.equal(intentView.intentIsWorthShowing({ ...plain, evidence: [entry('tag_no_places')] }), true);
assert.equal(intentView.intentIsWorthShowing(null), false);
const hybrid = { ...plain, original: 'Bakery and bookstore', hybrid: true, components: [comp('bakery'), comp('bookstore')],
  evidence: [entry('exact'), entry('tag_no_places', { phrase: 'bookstore', role: 'secondary', placeCount: 0 })],
  overlap: { established: false, sharedPlaces: [], statement: 'Overlap not established: no places were retrieved for bookstore.' },
  substitutions: ['Showing general bakery evidence; vegan-specific relevance is not verified by Qloo\'s category.'] };
const exported = renderBrief({ ...result, intent: hybrid }, [concept]).split('\n');
assert.ok(exported.includes('Businesses: bakery + bookstore (a combination)'));
assert.ok(exported.some(line => line.includes('bookstore') && line.includes('Category exists') && line.includes('0 returned places')), 'Each business keeps its own evidence line');
assert.ok(exported.some(line => line.startsWith('Overlap: Overlap not established')), 'No overlap is manufactured');
assert.ok(exported.some(line => line.startsWith('Simplified or not verified: Showing general bakery')));
assert.equal(renderBrief(result, [concept]).includes('How the idea was read'), false, 'An answer with no reading exports exactly as before');
console.log('[ok] The idea reading is shown only when informative, and exports each business, the overlap and every simplification.');

// --- what Qloo contributed: derived from the exploration, never claimed -------------------------------------
{
  const evidenceUrl = summary.url;
  const { module: diff } = await loadTs('../src/qlooDifference.ts', { "'./evidenceSummary'": `'${evidenceUrl}'` });
  const lead = { id: 'a', name: 'Lead', decisions: [{ evidenceIds: ['p1'] }, { evidenceIds: ['missing'] }], evidenceIds: ['p1'] };
  const other = { id: 'b', name: 'Other', decisions: [], evidenceIds: [] };
  const base = { concepts: [lead, other], evidence: [{ id: 'p1', kind: 'entity' }, { id: 't1', kind: 'tag' }],
    agent: { mode: 'frontier_ai', model: 'm', status: 'complete', modelCalls: 3, stoppingReason: 'done', rejectedClaims: [{}],
      steps: [{ index: 1, tool: 'rank', question: 'Does it rank?', reason: 'r', status: 'ok', resultCount: 3, cached: false },
              { index: 2, tool: 'recommend', question: 'q', reason: 'r', status: 'rejected', resultCount: 0, cached: false },
              { index: 3, tool: 'finish', question: '', reason: 'r', status: 'ok', resultCount: 0, cached: false }],
      analysis: { claims: [{}, {}], recommendedDirectionId: 'b' } } };
  const d = diff.qlooDifference(base, [lead, other], null);
  assert.equal(d.cited.numerator, 1); assert.equal(d.cited.denominator, 2);
  assert.equal(d.places, 1); assert.equal(d.signals, 1);
  assert.equal(d.steps.length, 1, 'finish and refused steps are not counted as evidence'); assert.equal(d.notRun, 1);
  assert.equal(d.agent.by, 'model'); assert.equal(d.agent.rejected, 1);
  assert.equal(d.pushback.kind, 'agent-differs');
  const contested = diff.qlooDifference(base, [lead, other], { directions: [{ directionId: 'a', verdict: 'contested', reason: 'Ranked 8 of 10.' }] });
  assert.equal(contested.pushback.kind, 'contested'); assert.match(contested.pushback.text, /Ranked 8 of 10/);
  const reordered = diff.qlooDifference(base, [other, lead], { directions: [{ directionId: 'b', verdict: 'supported', reason: '' }] });
  assert.equal(reordered.pushback.kind, 'reordered');
  const both = diff.qlooDifference(base, [other, lead], { directions: [{ directionId: 'b', verdict: 'unproven', reason: 'One check is missing.' }] });
  assert.equal(both.pushback.kind, 'unproven'); assert.match(both.pushback.text, /changed the order: Lead led before/);
  const rules = diff.qlooDifference({ ...base, agent: { mode: 'rules', status: 'limited', modelCalls: 0, stoppingReason: 'rules', steps: [] } }, [lead], null);
  assert.equal(rules.agent.by, 'rules'); assert.equal(rules.steps.length, 0);
  assert.equal(diff.qlooDifference(base, [], null), null);
  console.log('[ok] The Qloo-contribution strip counts only cited, run, evidence-bearing steps and can report pushback.');
}

{
  // A judge must be able to reach the map from the places it describes, and the
  // laptop-width layouts must not push the page sideways.
  const app = readFileSync(new URL('../src/components/Results.tsx', import.meta.url), 'utf8');
  assert.match(app, /Open the interest map/, 'the places section offers the map');
  assert.match(app, /setInsightTab\('map'\);onView\('roots'\)/, 'that offer opens the map tab of the roots section');
  const dusk = readFileSync(new URL('../src/dusk.css', import.meta.url), 'utf8');
  assert.match(dusk, /@media \(max-width: 1180px\)[^}]*\.topbar \{ min-width: 0; \}/, 'the topbar can shrink at laptop widths');
  const wild = readFileSync(new URL('../src/wildroot.css', import.meta.url), 'utf8');
  assert.match(wild, /@media \(max-width: 1180px\) \{\s*\.ox-body \{ grid-template-columns: minmax\(0, 1fr\); \}/, 'the map keeps its width at laptop widths');
  console.log('[ok] The map is reachable from the places section, and laptop widths neither overflow nor squeeze the map.');
}

// ---- rewording the idea: the way out of an answer that could not read it
const { checkReword, IDEA_MAX_LENGTH } = (await loadTs('../src/rewordIdea.ts')).module;
const idea = 'Pay-by-the-hour darkroom for film photographers';
const refused = (next) => { const r = checkReword(idea, next); assert.equal(r.ok, false, `should refuse: ${JSON.stringify(next)}`); assert.ok(r.message.length > 10, 'a refusal must say why'); return r };
for (const bad of ['', '   ', 'ab', ' a ', '\n\t']) refused(bad);
refused(idea);                                   // unchanged
refused(`  ${idea.toUpperCase()}  `);               // unchanged apart from case and padding
refused('Pay-by-the-hour   darkroom  for film\nphotographers'); // unchanged apart from whitespace
refused('x'.repeat(IDEA_MAX_LENGTH + 1));
assert.match(refused('x'.repeat(IDEA_MAX_LENGTH + 5)).message, /165/, 'the message states the real length');
const good = checkReword(idea, '  Darkroom   cafe\nfor film photographers ');
assert.deepEqual(good, { ok: true, idea: 'Darkroom cafe for film photographers' });
assert.equal(checkReword(idea, 'x'.repeat(IDEA_MAX_LENGTH)).ok, true, 'exactly the limit is allowed');
assert.equal(checkReword('', 'Bakery').ok, true, 'an empty original accepts any real idea');
assert.equal(checkReword(idea, 'Café 🍕 pizza — 寿司').ok, true, 'non-Latin text and emoji are ideas too');
const app = readFileSync(new URL('../src/App.tsx', import.meta.url), 'utf8');
const resultsView = readFileSync(new URL('../src/components/Results.tsx', import.meta.url), 'utf8');
const clar = readFileSync(new URL('../src/components/Clarification.tsx', import.meta.url), 'utf8');
assert.match(resultsView, /<RewordIdea current=\{result\.project\.businessIdea/, 'the empty answer offers the reword form');
assert.match(app, /onRewordIdea=\{\(idea\) => \{ void create\(\{ \.\.\.result\.project, businessIdea: idea \}\)/, 'rewording re-runs the same brief with only the idea changed');
assert.match(clar, /<RewordIdea current=\{idea\} onReword=\{onUseIdea\}/, 'the clarification offers the reword form');
console.log('[ok] Rewording refuses empty, tiny, over-long and unchanged ideas with a reason, normalises whitespace, and is wired into both dead ends.');
