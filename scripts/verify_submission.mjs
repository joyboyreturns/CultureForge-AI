#!/usr/bin/env node
/** Read-only packaging checks. --release additionally checks public deployment. */
import { existsSync, readFileSync } from 'node:fs';

const root = new URL('../', import.meta.url);
const release = process.argv.includes('--release');
let failures = 0;
function check(label, condition) {
  console.log(`${condition ? '[ok]' : '[FAIL]'} ${label}`);
  if (!condition) failures++;
}
function read(path) { return readFileSync(new URL(path, root), 'utf8'); }

for (const path of ['LICENSE', 'README.md', 'CHANGELOG.md', 'THIRD_PARTY_NOTICES.md', 'Dockerfile',
  'docker-compose.yml', 'render.yaml', 'docs/DEPLOY.md', 'docs/SUBMISSION.md', 'docs/DEMO.md',
  'docs/JUDGING_DAY.md', 'docs/BUSINESS.md', 'docs/INVESTOR_BRIEF.md', 'docs/RELEASE_AUDIT.md', 'docs/EVIDENCE_POLICY.md', 'docs/ARCHITECTURE.md',
  'docs/API.md', 'docs/LIMITATIONS.md', 'fonts/OFL.txt', 'dist/index.html', 'dist/studio/index.html']) {
  check(`Packaged: ${path}`, existsSync(new URL(path, root)));
}
check('GitHub-detectable MIT license', /MIT License/.test(read('LICENSE')));
check('No browser mock fallback', !/mockGenerate|mockData/.test(read('src/api.ts')));
check('Page visits do not run the example automatically', !/setTimeout\(runPulse/.test(read('main.js')));
check('Conservative example Qloo limits', /QLOO_MAX_CALLS_PER_HOUR=20/.test(read('.env.example'))
  && /QLOO_MAX_CALLS_PER_DAY=100/.test(read('.env.example')));

const manifest = JSON.parse(read('submission.json'));
if (release) {
  check('Owner confirmed eligibility', manifest.ownerConfirmedEligibility === true);
  check('Owner confirmed asset rights', manifest.ownerConfirmedAssetRights === true);
  let demo;
  try { demo = new URL(manifest.publicDemoUrl); } catch { /* Report a missing URL below. */ }
  const host = demo?.hostname ?? '';
  const publicHttps = demo?.protocol === 'https:' && host.includes('.')
    && !/localhost|\.local$|\.internal$|\.test$|\.example$|\.invalid$|^127\.|^10\.|^192\.168\.|^172\.(1[6-9]|2\d|3[01])\.|^169\.254\.|^0\.|:/.test(host);
  check('Public HTTPS demo URL recorded in submission.json', publicHttps);
  if (publicHttps) {
    for (const path of ['/', '/studio/', '/api/health', '/api/qloo/workflows']) {
      try {
        const response = await fetch(new URL(path, demo), { signal: AbortSignal.timeout(15000) });
        check(`Public GET ${path} succeeds`, response.ok);
        if (path === '/api/health' && response.ok) {
          const health = await response.json();
          check('Published API configured for real Qloo', health.dataMode === 'live' && health.providerReady === true);
        } else if (response.ok && path.endsWith('/')) {
          check(`${path} serves HTML`, (response.headers.get('content-type') ?? '').includes('text/html'));
        }
      } catch {
        check(`Public GET ${path} reachable`, false);
      }
    }
  }
} else {
  console.log('\nPackaging checks only. Public deployment and owner confirmations are still required.');
}
console.log('\nThis check sends no Qloo or model requests. After publishing, run scripts/smoke_test.py and click through docs/DEMO.md.');
process.exitCode = failures ? 1 : 0;
