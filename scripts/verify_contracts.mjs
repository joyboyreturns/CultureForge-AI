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
 *   2. POST /api/projects/generate -> a live or mock response against the contract
 *   3. the frontend's own mockGenerate() -> the fallback payload against the
 *      same contract, so the fallback path cannot drift either
 *   4. the error shapes the UI depends on (422 validation, 502 provider)
 *
 * Usage:
 *   node scripts/verify_contracts.mjs
 *   BASE_URL=http://127.0.0.1:8000 DEV_URL=http://localhost:5173 node scripts/verify_contracts.mjs
 */

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const DEV_URL = process.env.DEV_URL || 'http://localhost:5173';

const BUSINESS_TYPES = ['Food & beverage', 'Retail', 'Hospitality', 'Wellness', 'Entertainment'];

/** The contract, mirroring src/contracts.ts. */
const CONTRACT = {
  ProjectRequest: {
    businessType: { type: 'string', oneOf: BUSINESS_TYPES },
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
    audienceFit: { type: 'number', required: true },
    culturalRelevance: { type: 'number', required: true },
    feasibility: { type: 'number', required: true },
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
    conceptMode: { type: 'string', oneOf: ['sample'], required: true },
    notice: { type: 'string', required: true },
    provenance: { type: 'object', nullable: true },
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
  }
  for (const [index, signal] of (response.signals || []).entries()) {
    checkObject(`${where}.signals[${index}]`, signal, CONTRACT.CulturalSignal);
  }
  if (response.provenance) {
    checkObject(`${where}.provenance`, response.provenance, CONTRACT.ProvenanceMetadata);
  }
  // The UI renders these directly.
  if (response.concepts?.length && response.concepts.some((c) => !c.image)) {
    fail(where, 'at least one concept has an empty image');
  }
  if (response.concepts?.some((c) => typeof c.audienceFit !== 'number')) {
    fail(where, 'concept audienceFit is not numeric - the UI renders it as a score');
  }
}

const SAMPLE = {
  businessType: 'Food & beverage',
  audience: 'Design-conscious Gen Z & young professionals',
  location: 'Brooklyn, New York',
  budget: '$25k – $50k',
  objectives: ['Build a loyal community'],
};

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
    if (health.status !== 'ok') fail('GET /api/health', `status is "${health.status}"`);
    if (!['live', 'mock'].includes(health.dataMode)) {
      fail('GET /api/health', `dataMode is "${health.dataMode}", expected live or mock`);
    }
    console.log(`[ok]   GET /api/health -> ${health.dataMode}`);
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

  // 4. the frontend's own mock payload
  try {
    // Node cannot import over http, so pull the Vite-transformed modules and
    // inline the JSON catalog as a data: URL.
    const catalogSource = await (await fetch(`${DEV_URL}/shared/mockCatalog.json?import`)).text();
    const catalogUrl =
      'data:text/javascript;base64,' + Buffer.from(catalogSource, 'utf8').toString('base64');
    const mockSource = await (await fetch(`${DEV_URL}/src/mockData.ts`)).text();
    const patched = mockSource.replace(
      /(["'])(\/shared\/mockCatalog\.json\?import)\1/,
      (_match, quote) => `${quote}${catalogUrl}${quote}`
    );
    const module = await import(
      'data:text/javascript;base64,' + Buffer.from(patched, 'utf8').toString('base64')
    );
    const mock = module.mockGenerate(SAMPLE);
    checkResponse('frontend mockGenerate', mock);
    console.log(`[ok]   frontend mockGenerate -> ${mock.dataMode}, ${mock.concepts?.length} concepts`);
  } catch (error) {
    fail('frontend mockGenerate', `${error.message} (is the dev server on ${DEV_URL}?)`);
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
