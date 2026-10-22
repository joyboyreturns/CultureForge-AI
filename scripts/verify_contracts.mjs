#!/usr/bin/env node
/**
 * verify_contracts.mjs - check that the backend and the frontend agree.
 *
 * The frontend renders `GenerateResponse` directly (src/contracts.ts), so any
 * field the backend renames, drops, or retypes becomes a blank card or an
 * undefined at runtime with no compile-time error. This script pins the
 * contract on both sides and fails loudly when they drift.
 *
 * It checks:
 *   1. GET  /api/health          -> the provider mode shape
 *   2. POST /api/projects/generate -> a live response against the contract
 *   3. the frontend's API module -> it has no mock fallback, so what the
 *      studio shows is what Qloo returned
 *   4. the error shapes the UI depends on (422 validation, 502 provider)
 *
 * Usage:
 *   node scripts/verify_contracts.mjs
 *   BASE_URL=http://127.0.0.1:8000 node scripts/verify_contracts.mjs
 */

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const PROJECT_ROOT = new URL('..', import.meta.url);
const SRC_API = fileURLToPath(new URL('src/api.ts', PROJECT_ROOT));
const SRC_APP = fileURLToPath(new URL('src/App.tsx', PROJECT_ROOT));

const BUSINESS_TYPES = ['Food & beverage', 'Retail', 'Hospitality', 'Wellness', 'Entertainment'];

/** The contract, mirroring src/contracts.ts. */
const CONTRACT = {
  ProjectRequest: {
    businessType: { type: 'string', oneOf: BUSINESS_TYPES },
    businessIdea: { type: 'string' },
    audience: { type: 'string', minLength: 2 },
    location: { type: 'string', minLength: 2 },
    budget: { type: 'string' },
    objectives: { type: 'array' },
  },
  CulturalSignal: {
    label: { type: 'string', required: true },
    detail: { type: 'string', required: true },
    score: { type: 'number', nullable: true },
    affinity: { type: 'number', nullable: true },
    category: { type: 'string', required: true },
    provenance_id: { type: 'string', nullable: true },
  },
  ExperienceMoment: {
    title: { type: 'string', required: true },
    description: { type: 'string', required: true },
  },
  Concept: {
    id: { type: 'string', required: true },
    name: { type: 'string', required: true },
    tagline: { type: 'string', required: true },
    description: { type: 'string', required: true },
    audienceFit: { type: 'number', nullable: true },
    culturalRelevance: { type: 'number', nullable: true },
    feasibility: { type: 'number', nullable: true },
    budget: { type: 'string', required: true },
    investment: { type: 'string', required: true },
    signals: { type: 'array', required: true },
    accent: { type: 'string', required: true },
    image: { type: 'string', required: true },
    direction: { type: 'string', nullable: true },
    imageAlt: { type: 'string', nullable: true },
    personality: { type: 'string', nullable: true },
    audienceRationale: { type: 'string', nullable: true },
    implementationNote: { type: 'string', nullable: true },
    moments: { type: 'array' },
    evidenceIds: { type: 'array', required: true },
    decisions: { type: 'array', required: true },
    limitations: { type: 'array', required: true },
  },
  Evidence: {
    id: { type: 'string', required: true },
    kind: { type: 'string', oneOf: ['entity', 'tag', 'crossdomain'], required: true },
    presentation: { type: 'object', nullable: true },
    relevance: { type: 'object', nullable: true },
    label: { type: 'string', required: true },
    entityId: { type: 'string', nullable: true },
    entityType: { type: 'string', nullable: true },
    tagId: { type: 'string', nullable: true },
    affinity: { type: 'number', nullable: true },
    popularity: { type: 'number', nullable: true },
    rating: { type: 'number', nullable: true },
    priceLevel: { type: 'number', nullable: true },
    description: { type: 'string', nullable: true },
    image: { type: 'string', nullable: true },
    location: { type: 'string', nullable: true },
    traceId: { type: 'string', nullable: true },
  },
  Decision: {
    id: { type: 'string', required: true },
    field: { type: 'string', required: true },
    proposal: { type: 'string', required: true },
    evidenceIds: { type: 'array', required: true },
    ruleId: { type: 'string', required: true },
    origin: { type: 'string', oneOf: ['cultureforge_rule'], required: true },
  },
  TraceEvent: {
    id: { type: 'string', required: true },
    step: { type: 'string', required: true },
    workflow: { type: 'string', nullable: true },
    status: { type: 'string', oneOf: ['ok', 'needs_input', 'error', 'cached', 'skipped'], required: true },
    durationMs: { type: 'number', nullable: true },
    correlationId: { type: 'string', nullable: true },
    resultCount: { type: 'number', nullable: true },
    detail: { type: 'string', nullable: true },
    evidenceIds: { type: 'array', required: true },
    acquiredAt: { type: 'string', nullable: true },
    request: { type: 'object', nullable: true },
    resultExcerpt: { type: 'array', nullable: true },
  },
  Delivery: {
    kind: { type: 'string', oneOf: ['fresh', 'cache', 'snapshot', 'mock'], required: true },
    acquiredAt: { type: 'string', nullable: true },
    servedAt: { type: 'string', nullable: true },
    expiresAt: { type: 'string', nullable: true },
    transportRequests: { type: 'number', nullable: true },
    cachedIn: { type: 'string', oneOf: ['browser', 'server'], nullable: true },
  },
  ProvenanceMetadata: {
    source: { type: 'string', oneOf: ['Qloo API', 'Mock'], required: true },
    endpoint: { type: 'string', nullable: true },
    documentation: { type: 'string', nullable: true },
    resolved_tags: { type: 'array', required: true },
  },
  GenerateResponse: {
    projectId: { type: 'string', required: true },
    project: { type: 'object', required: true },
    concepts: { type: 'array', required: true },
    signals: { type: 'array', required: true },
    dataMode: { type: 'string', oneOf: ['mock', 'live'], required: true },
    conceptMode: { type: 'string', oneOf: ['sample', 'evidence_composed'], required: true },
    notice: { type: 'string', required: true },
    provenance: { type: 'object', nullable: true },
    evidence: { type: 'array', required: true },
    trace: { type: 'array', required: true },
    delivery: { type: 'object', nullable: true },
    composerVersion: { type: 'string', nullable: true },
  },
};

const failures = [];
const notes = [];

function fail(where, message) {
  failures.push(`${where}: ${message}`);
}

function checkObject(where, value, spec) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    fail(where, `expected an object, got ${Array.isArray(value) ? 'array' : typeof value}`);
    return;
  }
  for (const [field, rule] of Object.entries(spec)) {
    const actual = value[field];
    const missing = actual === undefined;
    if (missing) {
      if (rule.required) fail(where, `missing required field "${field}"`);
      continue;
    }
    if (rule.nullable && actual === null) continue;
    if (actual === null) {
      fail(where, `field "${field}" is null but not nullable`);
      continue;
    }
    if (rule.type === 'string' && typeof actual !== 'string') {
      fail(where, `field "${field}" should be a string, got ${typeof actual}`);
      continue;
    }
    if (rule.type === 'number' && typeof actual !== 'number') {
      fail(where, `field "${field}" should be a number, got ${typeof actual}`);
      continue;
    }
    if (rule.type === 'array' && !Array.isArray(actual)) {
      fail(where, `field "${field}" should be an array, got ${typeof actual}`);
      continue;
    }
    if (rule.type === 'object' && (typeof actual !== 'object' || Array.isArray(actual))) {
      fail(where, `field "${field}" should be an object`);
      continue;
    }
    if (rule.oneOf && !rule.oneOf.includes(actual)) {
      fail(where, `field "${field}" is "${actual}", expected one of ${rule.oneOf.join(' | ')}`);
    }
    if (rule.minLength && typeof actual === 'string' && actual.length < rule.minLength) {
      fail(where, `field "${field}" is shorter than ${rule.minLength}`);
    }
  }
  // Flag fields the contract does not know about: the frontend ignores them,
  // so they are usually a rename that only half landed.
  for (const field of Object.keys(value)) {
    if (!(field in spec)) {
      notes.push(`${where}: field "${field}" is not in the contract (frontend ignores it)`);
    }
  }
}

function checkResponse(where, response) {
  checkObject(where, response, CONTRACT.GenerateResponse);
  if (!response || typeof response !== 'object') return;
  checkObject(`${where}.project`, response.project, CONTRACT.ProjectRequest);
  for (const [index, concept] of (response.concepts || []).entries()) {
    checkObject(`${where}.concepts[${index}]`, concept, CONTRACT.Concept);
    for (const [m, moment] of (concept.moments || []).entries()) {
      checkObject(`${where}.concepts[${index}].moments[${m}]`, moment, CONTRACT.ExperienceMoment);
    }
    for (const [d, decision] of (concept.decisions || []).entries()) {
      checkObject(`${where}.concepts[${index}].decisions[${d}]`, decision, CONTRACT.Decision);
    }
  }
  for (const [index, signal] of (response.signals || []).entries()) {
    checkObject(`${where}.signals[${index}]`, signal, CONTRACT.CulturalSignal);
  }
  for (const [index, item] of (response.evidence || []).entries()) {
    checkObject(`${where}.evidence[${index}]`, item, CONTRACT.Evidence);
  }
  for (const [index, event] of (response.trace || []).entries()) {
    checkObject(`${where}.trace[${index}]`, event, CONTRACT.TraceEvent);
  }
  if (response.delivery) {
    checkObject(`${where}.delivery`, response.delivery, CONTRACT.Delivery);
  }
  if (response.provenance) {
    checkObject(`${where}.provenance`, response.provenance, CONTRACT.ProvenanceMetadata);
  }

  // Every evidence reference must resolve, and every cited decision must point
  // at evidence that actually exists. A dangling reference is the exact way a
  // "real data" claim turns out to be fake.
  const evidenceIds = new Set((response.evidence || []).map((e) => e.id));
  for (const [index, concept] of (response.concepts || []).entries()) {
    for (const id of concept.evidenceIds || []) {
      if (!evidenceIds.has(id)) {
        fail(where, `concepts[${index}].evidenceIds references unknown evidence "${id}"`);
      }
    }
    for (const [d, decision] of (concept.decisions || []).entries()) {
      for (const id of decision.evidenceIds || []) {
        if (!evidenceIds.has(id)) {
          fail(where, `concepts[${index}].decisions[${d}] references unknown evidence "${id}"`);
        }
      }
      if (!decision.evidenceIds?.length) {
        fail(where, `concepts[${index}].decisions[${d}] cites no evidence`);
      }
    }
  }

  // The UI renders these directly.
  if (response.concepts?.length && response.concepts.some((c) => !c.image)) {
    fail(where, 'at least one concept has an empty image');
  }

  // Mode-aware: sample concepts keep their numeric scores, evidence-composed
  // ones must not invent a business-fit percentage.
  if (response.conceptMode === 'evidence_composed') {
    for (const [index, concept] of (response.concepts || []).entries()) {
      if (typeof concept.audienceFit === 'number') {
        fail(where, `concepts[${index}] has a numeric audienceFit but conceptMode is evidence_composed`);
      }
      if (!concept.evidenceIds?.length) {
        fail(where, `concepts[${index}] has no evidence attached`);
      }
    }
  } else {
    for (const [index, concept] of (response.concepts || []).entries()) {
      if (typeof concept.audienceFit !== 'number') {
        fail(where, `concepts[${index}].audienceFit is not numeric but conceptMode is "${response.conceptMode}"`);
      }
    }
  }
}

// The first prepared brief, which scripts/prewarm.py keeps held. Run this
// against a backend with QLOO_LIVE_ENABLED=false to be sure it spends nothing.
const SAMPLE = JSON.parse(readFileSync(fileURLToPath(new URL('shared/demoBriefs.json', PROJECT_ROOT)), 'utf8')).briefs[0].project;

async function main() {
  console.log('='.repeat(64));
  console.log(' CultureForge — backend / frontend contract verification');
  console.log('='.repeat(64));

  // 1. health
  let health = null;
  try {
    const response = await fetch(`${BASE_URL}/api/health`);
    health = await response.json();
    if (response.status !== 200) fail('GET /api/health', `expected 200, got ${response.status}`);
    if (health.status !== 'ok') fail('GET /api/health', `status is "${health.status}": ${health.reason ?? ''}`);
    if (health.dataMode !== 'live') {
      fail('GET /api/health', `dataMode is "${health.dataMode}", expected live`);
    }
    if (health.providerReady === false) {
      fail('GET /api/health', `the backend cannot answer with live evidence: ${health.reason ?? 'no reason given'}`);
    }
    console.log(`[ok]   GET /api/health -> ${health.dataMode}, ${health.workflows?.length ?? 0} workflows`);
  } catch (error) {
    fail('GET /api/health', `not reachable at ${BASE_URL} (${error.message})`);
  }

  // 2. the /health alias tooling probes
  try {
    const response = await fetch(`${BASE_URL}/health`);
    if (response.status !== 200) fail('GET /health', `expected 200, got ${response.status}`);
    else console.log('[ok]   GET /health alias -> 200');
  } catch (error) {
    fail('GET /health', error.message);
  }

  // 3. a real generation
  try {
    const response = await fetch(`${BASE_URL}/api/projects/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(SAMPLE),
    });
    const body = await response.json();
    if (response.status !== 200) {
      fail('POST /api/projects/generate', `expected 200, got ${response.status}: ${JSON.stringify(body).slice(0, 200)}`);
    } else {
      checkResponse('POST /api/projects/generate', body);
      console.log(
        `[ok]   POST /api/projects/generate -> ${body.dataMode}, ` +
          `${body.concepts?.length} concepts, ${body.signals?.length} signals`
      );
    }
  } catch (error) {
    fail('POST /api/projects/generate', error.message);
  }

  // 4. the frontend has no mock fallback
  try {
    const api = readFileSync(SRC_API, 'utf8');
    const app = readFileSync(SRC_APP, 'utf8');
    if (/mockGenerate|mockData/.test(api) || /mockGenerate|mockData/.test(app)) {
      fail('frontend mock fallback', 'the studio still reaches for a mock generator');
    } else if (!/export async function generateConcepts/.test(api)) {
      fail('frontend mock fallback', 'src/api.ts no longer exports generateConcepts');
    } else if (!/export function heldResult/.test(api)) {
      fail('frontend mock fallback', 'src/api.ts no longer holds real answers for the browser');
    } else {
      console.log('[ok]   the frontend has no mock fallback -> real data, or a stated error');
    }
  } catch (error) {
    fail('frontend mock fallback', error.message);
  }

  // 5. the error shape the UI depends on
  try {
    const response = await fetch(`${BASE_URL}/api/projects/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ businessType: 'Not A Type', audience: 'x' }),
    });
    const body = await response.json();
    if (response.status !== 422) {
      fail('POST invalid payload', `expected 422, got ${response.status}`);
    } else if (typeof body.detail !== 'string') {
      fail('POST invalid payload', `detail should be a readable string, got ${typeof body.detail}`);
    } else {
      console.log(`[ok]   422 detail is readable -> "${body.detail.slice(0, 60)}..."`);
    }
  } catch (error) {
    fail('POST invalid payload', error.message);
  }

  console.log('-'.repeat(64));
  if (notes.length) {
    console.log('notes:');
    for (const note of notes) console.log(`  - ${note}`);
  }
  if (failures.length) {
    console.log(`FAILED (${failures.length}):`);
    for (const failure of failures) console.log(`  x ${failure}`);
    console.log('-'.repeat(64));
    process.exitCode = 1;
    return;
  }
  console.log('All contract checks passed.');
  console.log('-'.repeat(64));
}

main();
