// Records the animated diagram scenes. Usage: node record_diagrams.cjs <outDir> [scene ...]
const { createRequire } = require('module'); const fs = require('fs'); const path = require('path');
const { chromium } = createRequire('/Users/vincent/Documents/AccessRipple/package.json')('playwright');
const OUT = process.argv[2]; const ONLY = process.argv.slice(3);
const PAGE = 'file://' + '/Users/vincent/Documents/CultureForge AI/artifacts/demo-video/diagrams/diagrams.html'.replace(/ /g, '%20');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  fs.mkdirSync(path.join(OUT, 'raw'), { recursive: true });
  const man = fs.existsSync(path.join(OUT, 'manifest.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'manifest.json'))) : {};
  for (const n of ['compare', 'pipeline', 'verdict', 'layers'].filter((x) => !ONLY.length || ONLY.includes(x))) {
    const dir = path.join(OUT, 'raw', 'd-' + n); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir, size: { width: 1920, height: 1080 } } });
    const t0 = Date.now(); const p = await ctx.newPage();
    await p.goto(PAGE + '#' + n); await p.reload(); await p.waitForFunction(() => window.ready); await sleep(500);
    const markAt = (Date.now() - t0) / 1000;
    await p.evaluate(() => window.go());
    const dur = await p.evaluate(() => window.sceneDuration);
    await sleep(dur * 1000 + 1200);
    const vid = p.video(); await ctx.close(); const file = await vid.path(); await browser.close();
    fs.copyFileSync(file, path.join(OUT, 'raw', 'd-' + n + '.webm'));
    man['d-' + n] = { markAt, dur }; fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(man, null, 2));
    console.log('recorded', n, 'start', markAt.toFixed(1), 's, length', (dur + 1.2).toFixed(1), 's');
  }
})();
