/**
 * The landing page's background, drawn in code.
 *
 * An original scene made for CultureForge, with no video, photograph or other third-party
 * media: a dusk sky, a faint field of drifting glyphs (the signals the product reads), and three
 * dunes whose ridgelines move slowly. Everything is generated from sine waves and a small
 * hash function, so it is the same on every visit and weighs a few kilobytes.
 *
 *   startScene(canvas, { animate })
 *
 * `animate: false` draws one still frame (reduced motion). The scene pauses while the tab is
 * hidden and runs at about 30 frames a second.
 */

const GLYPHS = '08S#$%&XO';

function hash(a, b, c) {
  let h = (a * 374761393 + b * 668265263 + c * 2147483647) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

export function startScene(canvas, options) {
  const animate = !options || options.animate !== false;
  const context = canvas.getContext('2d', { alpha: false });
  if (!context) return function stop() {};

  const glyphLayer = document.createElement('canvas');
  const glyphContext = glyphLayer.getContext('2d');
  let width = 0;
  let height = 0;
  let cell = 24;
  let lastGlyphPaint = -1;

  function resize() {
    const box = canvas.getBoundingClientRect();
    const cssWidth = Math.max(320, box.width || window.innerWidth);
    const cssHeight = Math.max(240, box.height || window.innerHeight);
    // At most 1280 pixels wide: it is a soft backdrop, and the grain layer above hides the scaling.
    const scale = Math.min(1, 1280 / cssWidth);
    width = canvas.width = Math.round(cssWidth * scale);
    height = canvas.height = Math.round(cssHeight * scale);
    glyphLayer.width = width;
    glyphLayer.height = height;
    cell = Math.max(13, Math.round(width / 76));
    lastGlyphPaint = -1;
  }

  /** A ridgeline: a broad bump plus two slow waves, as heights in pixels from the top. */
  function ridge(x, time, base, bump, bumpAt, bumpWidth, wave, phase) {
    const u = x / width;
    const hill = bump * Math.exp(-Math.pow((u - bumpAt) / bumpWidth, 2));
    const drift =
      wave * Math.sin(u * 3.1 + phase + time * 0.06) +
      wave * 0.45 * Math.sin(u * 7.3 + phase * 1.7 - time * 0.045);
    return height * (base - hill) + drift * height;
  }

  function paintSky() {
    const sky = context.createLinearGradient(0, 0, 0, height * 0.62);
    sky.addColorStop(0, '#7f7cb2');
    sky.addColorStop(0.22, '#a9a2cf');
    sky.addColorStop(0.38, '#e4dbe0');
    sky.addColorStop(0.56, '#e79db6');
    sky.addColorStop(0.72, '#dc8458');
    sky.addColorStop(1, '#5a3358');
    context.fillStyle = sky;
    context.fillRect(0, 0, width, height);
    // A warm bloom behind the largest dune.
    const bloom = context.createRadialGradient(width * 0.5, height * 0.22, 0, width * 0.5, height * 0.22, width * 0.5);
    bloom.addColorStop(0, 'rgba(255, 246, 232, 0.5)');
    bloom.addColorStop(1, 'rgba(255, 250, 238, 0)');
    context.fillStyle = bloom;
    context.fillRect(0, 0, width, height);
  }

  function paintGlyphs(time) {
    // The field is repainted a few times a second and then simply drifted, which is cheaper than
    // filling several hundred characters every frame and reads as a slow flicker.
    const bucket = Math.floor(time * 2.5);
    if (bucket === lastGlyphPaint) return;
    lastGlyphPaint = bucket;
    const g = glyphContext;
    g.clearRect(0, 0, width, height);
    g.font = '600 ' + Math.round(cell * 0.78) + 'px "SFMono-Regular", Menlo, Consolas, monospace';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    const columns = Math.ceil(width / cell);
    const rows = Math.ceil((height * 0.62) / cell);
    for (let row = 0; row < rows; row += 1) {
      const y = row * cell + cell / 2;
      // Dense and bright near the top, thinning to nothing at the horizon.
      const density = Math.max(0, 1 - y / (height * 0.5)) * 0.8;
      for (let column = 0; column < columns; column += 1) {
        const slot = Math.floor(time * (0.4 + hash(column, row, 7) * 0.9) + hash(column, row, 3) * 10);
        if (hash(column, row, slot) > density) continue;
        const glyph = GLYPHS.charAt(Math.floor(hash(column, row, slot + 99) * GLYPHS.length));
        g.fillStyle = 'rgba(255, 255, 255, ' + (0.28 + hash(column, row, slot + 5) * 0.5).toFixed(2) + ')';
        g.fillText(glyph, column * cell + cell / 2, y);
      }
    }
  }

  function dune(time, spec) {
    context.beginPath();
    context.moveTo(0, height);
    const step = Math.max(6, Math.round(width / 160));
    for (let x = 0; x <= width + step; x += step) {
      context.lineTo(x, ridge(x, time, spec.base, spec.bump, spec.at, spec.span, spec.wave, spec.phase));
    }
    context.lineTo(width, height);
    context.closePath();
    const top = height * (spec.base - spec.bump);
    const fill = context.createLinearGradient(0, top, 0, top + height * spec.depth);
    fill.addColorStop(0, spec.rim);
    fill.addColorStop(0.18, spec.crest);
    fill.addColorStop(1, spec.shade);
    context.fillStyle = fill;
    context.fill();
  }

  function paint(time) {
    paintSky();
    paintGlyphs(time);
    context.drawImage(glyphLayer, 0, Math.sin(time * 0.2) * 2);
    // Far, middle, near: each darker and warmer at its edge than the one behind.
    dune(time, { base: 0.58, bump: 0.25, at: 0.5, span: 0.3, wave: 0.012, phase: 0.4, depth: 0.55,
      rim: '#d9779a', crest: '#6f4a86', shade: '#241638' });
    dune(time, { base: 0.76, bump: 0.07, at: 0.84, span: 0.34, wave: 0.016, phase: 2.1, depth: 0.42,
      rim: '#e8896a', crest: '#9a4d72', shade: '#1a0e1f' });
    dune(time, { base: 0.9, bump: 0.13, at: 0.12, span: 0.3, wave: 0.014, phase: 4.2, depth: 0.3,
      rim: '#f0a07a', crest: '#7a3a5c', shade: '#07040a' });
    // Everything below the dunes falls to black, as the page's text sits over it.
    const floor = context.createLinearGradient(0, height * 0.72, 0, height);
    floor.addColorStop(0, 'rgba(0, 0, 0, 0)');
    floor.addColorStop(1, 'rgba(0, 0, 0, 0.92)');
    context.fillStyle = floor;
    context.fillRect(0, height * 0.72, width, height * 0.28);
  }

  resize();
  window.addEventListener('resize', resize);
  const started = performance.now();
  paint(0);
  canvas.classList.add('is-playing');
  if (!animate) {
    return function stop() { window.removeEventListener('resize', resize); };
  }

  let frame = 0;
  let last = 0;
  function tick(now) {
    frame = window.requestAnimationFrame(tick);
    if (document.hidden || now - last < 33) return;
    last = now;
    paint((now - started) / 1000);
  }
  frame = window.requestAnimationFrame(tick);
  return function stop() {
    window.cancelAnimationFrame(frame);
    window.removeEventListener('resize', resize);
  };
}
