// Records the demo clips by driving the real app. Usage: node record.cjs <outDir> [clipName ...]
const { createRequire } = require('module');
const fs = require('fs');
const path = require('path');
const { chromium } = createRequire('/Users/vincent/Documents/AccessRipple/package.json')('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:4174';
const OUT = process.argv[2];
const ONLY = process.argv.slice(3);
const W = 1600, H = 900;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const CURSOR = `
(() => {
  const mk = () => {
    if (document.getElementById('__cur')) return;
    const c = document.createElement('div'); c.id = '__cur';
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M3 2l7.5 19 2.7-7.6L21 10.7z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, { position: 'fixed', left: '0', top: '0', zIndex: 2147483647, pointerEvents: 'none', transform: 'translate(-100px,-100px)', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,.45))' });
    document.documentElement.appendChild(c);
    const ring = document.createElement('div'); ring.id = '__ring';
    Object.assign(ring.style, { position: 'fixed', left: '0', top: '0', width: '34px', height: '34px', margin: '-12px 0 0 -12px', borderRadius: '50%', border: '2px solid rgba(199,163,255,.95)', zIndex: 2147483646, pointerEvents: 'none', opacity: '0', transition: 'opacity .35s, transform .35s' });
    document.documentElement.appendChild(ring);
    addEventListener('mousemove', (e) => { c.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)'; }, true);
    addEventListener('mousedown', (e) => {
      ring.style.transition = 'none'; ring.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px) scale(.6)'; ring.style.opacity = '1';
      requestAnimationFrame(() => requestAnimationFrame(() => { ring.style.transition = 'opacity .5s, transform .5s'; ring.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px) scale(1.6)'; ring.style.opacity = '0'; }));
    }, true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mk); else mk();
})();`;

async function newClip(name) {
  const dir = path.join(OUT, 'raw', name); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir, size: { width: W, height: H } } });
  await ctx.addInitScript(CURSOR);
  const t0 = Date.now();
  const p = await ctx.newPage();
  let x = W / 2, y = H / 2;
  const api = {
    p,
    markAt: 0,
    mark() { api.markAt = (Date.now() - t0) / 1000; },
    async goto(url) { await p.goto(url); await p.waitForTimeout(1500); await p.mouse.move(x, y); },
    async moveTo(loc, opts = {}) {
      const el = typeof loc === 'string' ? p.locator(loc).first() : loc.first();
      await el.scrollIntoViewIfNeeded().catch(() => {});
      const b = await el.boundingBox(); if (!b) return;
      const tx = b.x + b.width * (opts.fx ?? 0.5), ty = b.y + b.height * (opts.fy ?? 0.5);
      await p.mouse.move(tx, ty, { steps: opts.steps ?? 28 }); x = tx; y = ty; await sleep(opts.after ?? 350);
    },
    async click(loc, opts = {}) { await api.moveTo(loc, opts); await p.mouse.down(); await sleep(80); await p.mouse.up(); await sleep(opts.settle ?? 600); },
    async scroll(total, ms, at = [W * 0.6, H * 0.6]) {
      await p.mouse.move(at[0], at[1], { steps: 8 }); x = at[0]; y = at[1];
      // Time-based: each wheel call has its own latency, so aim at where the scroll should be by now.
      const start = Date.now(); let done = 0;
      while (true) {
        const t = Math.min(1, (Date.now() - start) / ms);
        const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        const want = Math.round(total * ease);
        if (want - done !== 0) { await p.mouse.wheel(0, want - done); done = want; }
        if (t >= 1) break;
        await sleep(16);
      }
    },
    async finish(hold = 1200) {
      await sleep(hold);
      const vid = p.video(); await ctx.close(); const file = await vid.path(); await browser.close();
      const target = path.join(OUT, 'raw', name + '.webm'); fs.copyFileSync(file, target);
      return { name, file: target, markAt: api.markAt };
    },
  };
  return api;
}

async function openExample(c) {
  await c.goto(BASE + '/studio/');
  await c.click(c.p.getByRole('button', { name: /Run the example brief/ }), { settle: 500 });
  await c.p.waitForTimeout(9000);
}
const rail = (c, label) => c.click(c.p.locator('.section-rail button', { hasText: label }), { settle: 1500 });

const CLIPS = {
  // 01 ~24s
  async landing(c) {
    await c.goto(BASE + '/'); await sleep(2500); c.mark();
    await sleep(4000);
    const h = await c.p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    await c.scroll(Math.min(h, 2600), 15000);
    await sleep(1500);
  },
  // 02 ~24s
  async studio(c) {
    await c.goto(BASE + '/studio/'); await sleep(2500); c.mark();
    await sleep(2500);
    await c.click(c.p.getByRole('button', { name: /Run the example brief/ }), { settle: 500 });
    await sleep(8500);
    await c.scroll(700, 6000);
    await sleep(1500);
    await c.scroll(600, 5000);
  },
  // 03 ~20s
  async places(c) {
    await openExample(c); await rail(c, 'Places & signals'); c.mark();
    await sleep(2500);
    await c.scroll(520, 4500);
    await sleep(1500);
    await c.scroll(520, 4500);
    await sleep(2000);
  },
  // 04 ~14s
  async directions(c) {
    await openExample(c); await rail(c, 'Directions'); c.mark();
    await sleep(2500);
    await c.scroll(600, 5000);
    await sleep(1500);
    await c.scroll(600, 5000);
  },
  // 05 ~34s
  async map(c) {
    await openExample(c); await rail(c, 'Places & signals');
    await c.scroll(1400, 2500);
    await sleep(500); c.mark();
    await c.click(c.p.getByRole('button', { name: /Open the interest map/ }), { settle: 500 });
    await sleep(9000);
    await c.p.locator('.ox-canvas').scrollIntoViewIfNeeded(); await sleep(1500);
    await c.click(c.p.locator('.ox-venue-btn', { hasText: 'No.4' }), { settle: 3500 });
    await c.scroll(500, 3500, [1380, 600]);
    await sleep(1000);
    await c.click(c.p.getByRole('button', { name: /What happens without this evidence/ }), { settle: 3500 });
    await c.scroll(450, 3500, [1380, 600]);
    await sleep(3500);
  },
  // 06 ~32s
  async test(c) {
    await openExample(c); await rail(c, 'Evidence test'); c.mark();
    await sleep(3000);
    await c.click(c.p.getByRole('button', { name: 'Test the evidence' }).last(), { settle: 500 });
    await sleep(9000);
    await c.scroll(460, 4000);
    await sleep(3500);
    await c.scroll(520, 4500);
    await sleep(3000);
  },
  // 07 ~26s
  async agent(c) {
    await openExample(c); await rail(c, 'Decision'); c.mark();
    await sleep(3500);
    await c.scroll(480, 4500);
    await sleep(3000);
    await c.scroll(600, 5000);
    await sleep(3000);
    await c.scroll(600, 5000);
  },
  // 08 ~14s
  async close(c) {
    await c.goto(BASE + '/'); await sleep(2000); c.mark();
    await sleep(3000);
    await c.moveTo(c.p.getByRole('link', { name: /Try the demo/ }).or(c.p.getByRole('button', { name: /Try the demo/ })), { steps: 40 });
    await sleep(6000);
  },
};

(async () => {
  fs.mkdirSync(path.join(OUT, 'raw'), { recursive: true });
  const names = Object.keys(CLIPS).filter((n) => !ONLY.length || ONLY.includes(n));
  const manifest = fs.existsSync(path.join(OUT, 'manifest.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'manifest.json'))) : {};
  for (const n of names) {
    process.stdout.write('recording ' + n + ' ... ');
    const c = await newClip(n);
    try { await CLIPS[n](c); } catch (e) { console.log('FAILED:', e.message.split('\n')[0]); }
    manifest[n] = await c.finish();
    console.log('done, content starts at', manifest[n].markAt.toFixed(1) + 's');
    fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2));
  }
})();
