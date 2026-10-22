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
const { renderBrief } = (await loadTs('../src/brief.ts', { "'./evidenceSummary'": `'${summary.url}'` })).module;
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
assert.equal(tour.TOUR_STEPS.length, 6);
console.log('[ok] Guided tour supports the brief before evidence exists and requires real evidence for the remaining interactions.');
