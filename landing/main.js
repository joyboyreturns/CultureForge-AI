/**
 * Intelligence Designed To Evolve — Main Script
 * Vanilla JS + Framer Motion (Motion engine) enhancements
 */

import demoBriefs from '../shared/demoBriefs.json';
import { startScene } from './landing-scene.js';

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // 1. Easing & Count-up Animation
  // ---------------------------------------------------------------------------
  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function startCountUp(element, target, suffix, decimals, duration, delay) {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      element.textContent = target.toFixed(decimals) + suffix;
      return;
    }

    setTimeout(() => {
      // If Framer Motion is available, use its precision animate runner; else RAF
      if (window.Motion && typeof window.Motion.animate === 'function') {
        window.Motion.animate(0, target, {
          duration: duration / 1000,
          ease: [0.22, 1, 0.36, 1],
          onUpdate: (latest) => {
            element.textContent = Number(latest).toFixed(decimals) + suffix;
          }
        }).finished.then(() => {
          element.textContent = target.toFixed(decimals) + suffix;
        });
      } else {
        const startTime = performance.now();
        function frame(now) {
          const elapsed = now - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const currentVal = easeOutCubic(progress) * target;
          element.textContent = currentVal.toFixed(decimals) + suffix;

          if (progress < 1) {
            requestAnimationFrame(frame);
          } else {
            element.textContent = target.toFixed(decimals) + suffix;
          }
        }
        requestAnimationFrame(frame);
      }
    }, delay);
  }

  function initStatsObserver() {
    const statCards = document.querySelectorAll('.stat-card');
    if (!statCards.length) return;

    let hasRun = false;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasRun) {
            hasRun = true;
            observer.disconnect();

            statCards.forEach((card, index) => {
              const valueEl = card.querySelector('.stat-value');
              if (!valueEl) return;

              const target = parseFloat(valueEl.getAttribute('data-target') || '0');
              const suffix = valueEl.getAttribute('data-suffix') || '';
              const decimals = parseInt(valueEl.getAttribute('data-decimals') || '0', 10);

              const duration = 1500 + index * 80;
              const delay = 480 + index * 90;

              startCountUp(valueEl, target, suffix, decimals, duration, delay);
            });
          }
        });
      },
      { threshold: 0.25 }
    );

    const footer = document.querySelector('.stats-footer');
    if (footer) {
      observer.observe(footer);
    } else {
      statCards.forEach((card) => observer.observe(card));
    }
  }

  // ---------------------------------------------------------------------------
  // 2. Mobile Menu (Sheet + Overlay + Burger)
  // ---------------------------------------------------------------------------
  function initMobileMenu() {
    const burgerBtn = document.querySelector('.burger-btn');
    const overlay = document.getElementById('mobile-overlay');
    const sheet = document.getElementById('mobile-menu');
    if (!burgerBtn || !overlay || !sheet) return;

    function openMenu() {
      burgerBtn.setAttribute('aria-expanded', 'true');
      overlay.removeAttribute('hidden');
      sheet.removeAttribute('hidden');
      document.body.classList.add('menu-open');

      if (window.Motion && typeof window.Motion.animate === 'function') {
        window.Motion.animate(
          sheet,
          { opacity: [0, 1], y: [-16, 0], scale: [0.96, 1] },
          { duration: 0.38, ease: [0.22, 1, 0.36, 1] }
        );
        window.Motion.animate(overlay, { opacity: [0, 1] }, { duration: 0.28, ease: 'easeOut' });
      }
    }

    function closeMenu() {
      burgerBtn.setAttribute('aria-expanded', 'false');

      if (window.Motion && typeof window.Motion.animate === 'function') {
        const animSheet = window.Motion.animate(
          sheet,
          { opacity: [1, 0], y: [0, -12], scale: [1, 0.97] },
          { duration: 0.2, ease: 'easeIn' }
        );
        const animOverlay = window.Motion.animate(overlay, { opacity: [1, 0] }, { duration: 0.2, ease: 'easeIn' });

        Promise.all([animSheet.finished, animOverlay.finished]).then(() => {
          overlay.setAttribute('hidden', '');
          sheet.setAttribute('hidden', '');
          document.body.classList.remove('menu-open');
        });
      } else {
        overlay.setAttribute('hidden', '');
        sheet.setAttribute('hidden', '');
        document.body.classList.remove('menu-open');
      }
    }

    burgerBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = burgerBtn.getAttribute('aria-expanded') === 'true';
      if (isOpen) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    overlay.addEventListener('click', closeMenu);

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && burgerBtn.getAttribute('aria-expanded') === 'true') {
        closeMenu();
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 720 && burgerBtn.getAttribute('aria-expanded') === 'true') {
        closeMenu();
      }
    });

    // Close on mobile links click
    const mobileLinks = sheet.querySelectorAll('.mobile-link, .mobile-signin-btn');
    mobileLinks.forEach((link) => {
      link.addEventListener('click', () => {
        closeMenu();
      });
    });
  }

  // ---------------------------------------------------------------------------
  // 3. Navigation Active State Synchronization
  // ---------------------------------------------------------------------------
  function initLandingNavigation() {
    const links = document.querySelectorAll('.nav-link, .mobile-link, .logo-btn[data-nav], .followup-link[data-nav], .scroll-cue[data-nav]');
    const views = document.querySelectorAll('[data-landing-view]');
    const followup = document.querySelector('[data-home-followup]');
    const validViews = new Set(Array.from(views, (view) => view.getAttribute('data-landing-view')));
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let transitionToken = 0;

    function showView(name, updateHistory = true, animate = true) {
      const target = validViews.has(name) ? name : 'home';
      const current = Array.from(views).find((view) => !view.hidden);
      const next = Array.from(views).find((view) => view.getAttribute('data-landing-view') === target);
      const token = ++transitionToken;

      function commit() {
        // A newer navigation superseded this transition.
        if (token !== transitionToken) return;
        views.forEach((view) => {
          view.hidden = true;
          view.classList.remove('view-enter', 'view-exit');
        });
        if (next) {
          next.hidden = false;
          if (animate) next.classList.add('view-enter');
        }
        if (followup) followup.hidden = target !== 'home';
        links.forEach((link) => {
          const active = link.getAttribute('data-nav') === target;
          link.classList.toggle('active', active);
          if (link.classList.contains('nav-link') || link.classList.contains('mobile-link')) {
            if (active) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
          }
        });
        document.querySelector('.page')?.setAttribute('data-active-view', target);
        if (updateHistory) history.pushState(null, '', `#${target}`);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }

      // Cross-fade: the outgoing view blurs out before the incoming one rises in.
      if (animate && current && current !== next && !reducedMotion) {
        current.classList.add('view-exit');
        window.setTimeout(commit, 280);
      } else {
        commit();
      }
    }

    links.forEach((link) => link.addEventListener('click', (event) => {
      const target = link.getAttribute('data-nav');
      if (!target) return;
      event.preventDefault();
      showView(target);
    }));
    window.addEventListener('popstate', () => showView(location.hash.slice(1), false));
    showView(location.hash.slice(1), false, false);
  }

  // The redesigned marketing entry remains the first screen; open the existing
  // React prototype for the creation, results, evidence, and scenario journey.
  function initPrototypeJourney() {
    const root = document.getElementById('root');
    const landing = document.querySelector('.page');
    const background = document.querySelector('.bg');
    const curtain = document.querySelector('.curtain');
    if (!root || !landing) return;
    let studioLoaded = false;
    let transitionTimer = null;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const WIPE_MS = reducedMotion ? 0 : 660;

    // Run `swap` while the curtain fully covers the screen, then lift it.
    function withCurtain(swap) {
      if (!curtain) { swap(); return; }
      if (transitionTimer) window.clearTimeout(transitionTimer);
      curtain.classList.add('is-covering');
      transitionTimer = window.setTimeout(function () {
        swap();
        // Let the studio settle before the curtain lifts.
        window.setTimeout(function () {
          curtain.classList.remove('is-covering');
        }, reducedMotion ? 0 : 180);
      }, WIPE_MS);
    }

    function openStudio(event) {
      event?.preventDefault();
      history.replaceState(null, '', '#workspace/create');
      document.body.classList.remove('menu-open');
      withCurtain(function () {
        document.body.classList.add('studio-mode');
        landing.hidden = true;
        if (background) background.hidden = true;
        root.hidden = false;
        root.style.display = 'block';
        if (!studioLoaded) {
          studioLoaded = true;
          import('/src/main.tsx').catch((error) => {
            studioLoaded = false;
            root.innerHTML = '<p class="studio-load-error">The exploration studio could not load. Refresh the page and try again.</p>';
            console.error('CultureForge studio failed to load:', error);
          });
        } else window.dispatchEvent(new Event('cultureforge:open-create'));
        window.scrollTo(0, 0);
      });
    }

    function showLanding() {
      history.replaceState(null, '', window.location.pathname + window.location.search);
      withCurtain(function () {
        root.hidden = true;
        root.style.display = 'none';
        landing.hidden = false;
        if (background) background.hidden = false;
        document.body.classList.remove('studio-mode');
        document.querySelectorAll('.stat-value[data-target]').forEach((element) => {
          const target = Number(element.getAttribute('data-target') || '0');
          const decimals = Number(element.getAttribute('data-decimals') || '0');
          const suffix = element.getAttribute('data-suffix') || '';
          element.textContent = target.toFixed(decimals) + suffix;
        });
        window.scrollTo(0, 0);
      });
    }

    document.querySelectorAll('[data-open-studio]:not([data-pulse-open])').forEach((link) => {
      link.addEventListener('click', openStudio);
    });

    // The live pulse's own link: it opens the exploration that was just
    // performed on this page, with the test that was run on it — not an empty
    // form the judge has to fill in again.
    const pulseLink = document.querySelector('[data-pulse-open]');
    if (pulseLink) {
      pulseLink.addEventListener('click', function (event) {
        event.preventDefault();
        openStudio(event);
        window.dispatchEvent(new CustomEvent('cultureforge:handoff', {
          detail: window.__cultureforgeHandoff || null,
        }));
      });
    }
    window.addEventListener('cultureforge:show-landing', showLanding);
    if (window.location.hash.startsWith('#workspace')) openStudio();
  }

  // ---------------------------------------------------------------------------
  // 4. Background scene (drawn in code, no video)
  // ---------------------------------------------------------------------------
  function initBackgroundVideo() {
    const canvas = document.querySelector('.bg-video');
    if (!canvas || typeof canvas.getContext !== 'function') return;
    // Reduced motion gets one still frame; everyone else gets the slow drift.
    const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    startScene(canvas, { animate: !still });
  }

  // ---------------------------------------------------------------------------
  // 5. Cinematic Layer
  // ---------------------------------------------------------------------------
  function initCinematic() {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const video = document.querySelector('.bg-video');
    const progress = document.querySelector('.scroll-progress > i');
    const navPill = document.querySelector('.nav-pill');
    const navGlow = document.querySelector('.nav-glow');
    const followup = document.querySelector('[data-home-followup]');

    // Scroll progress and video parallax share one rAF-throttled listener.
    let ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        const y = window.scrollY || 0;
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        if (progress) {
          // A view that barely scrolls would peg the bar at 100% straight
          // away, so hide it when there is not enough distance to matter.
          progress.parentElement.style.opacity = max < 140 ? '0' : '1';
          progress.style.width = Math.min(100, (y / max) * 100).toFixed(2) + '%';
        }
        if (video && !reducedMotion) {
          const shift = Math.max(-42, Math.min(42, y * 0.11));
          video.style.setProperty('--parallax', shift.toFixed(1) + 'px');
        }
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    onScroll();

    // The follow-up section rises into view as it arrives.
    if (followup && !reducedMotion && 'IntersectionObserver' in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('reveal');
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.2 });
      observer.observe(followup);
    }

    // A soft spotlight follows the hovered nav link.
    if (navPill && navGlow) {
      const navLinks = navPill.querySelectorAll('.nav-link');
      function moveGlow(link) {
        const pillRect = navPill.getBoundingClientRect();
        const rect = link.getBoundingClientRect();
        navGlow.style.setProperty('--glow-w', rect.width + 'px');
        navGlow.style.setProperty('--glow-x', (rect.left - pillRect.left) + 'px');
      }
      navLinks.forEach(function (link) {
        link.addEventListener('mouseenter', function () { moveGlow(link); });
        link.addEventListener('focus', function () { moveGlow(link); });
      });
      navPill.addEventListener('mouseleave', function () {
        navGlow.style.setProperty('--glow-w', '0px');
      });
    }

    // Pointer light and a gentle magnetic pull on the call to action.
    const ctas = document.querySelectorAll('.cta-btn');
    if (!reducedMotion && window.matchMedia('(pointer: fine)').matches) {
      ctas.forEach(function (cta) {
        cta.addEventListener('pointermove', function (event) {
          const rect = cta.getBoundingClientRect();
          // A hidden view reports a zero-sized rect; dividing by it would
          // produce NaN and break the transform.
          if (!rect.width || !rect.height) return;
          const x = (event.clientX - rect.left) / rect.width;
          const y = (event.clientY - rect.top) / rect.height;
          cta.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
          cta.style.setProperty('--my', (y * 100).toFixed(1) + '%');
          cta.style.transform =
            'translate(' + ((x - 0.5) * 8).toFixed(2) + 'px,' + (((y - 0.5) * 5) - 2).toFixed(2) + 'px) scale(1.015)';
        });
        cta.addEventListener('pointerleave', function () {
          cta.style.transform = '';
          cta.style.setProperty('--mx', '50%');
          cta.style.setProperty('--my', '50%');
        });
      });
    }
  }

  // ---------------------------------------------------------------------------
  // 6. Framer Motion / Motion Spring & Micro-Interactions
  // ---------------------------------------------------------------------------
  function initFramerMotionEnhancements() {
    if (!window.Motion || typeof window.Motion.animate !== 'function') return;
    const { animate } = window.Motion;

    // Avatar ring spring hover lifts
    const avatars = [
      { el: document.querySelector('.avatar-ring.a1'), lift: -2 },
      { el: document.querySelector('.avatar-ring.a2'), lift: -4 },
      { el: document.querySelector('.avatar-ring.a3'), lift: -2 }
    ];

    avatars.forEach(({ el, lift }) => {
      if (!el) return;
      el.addEventListener('mouseenter', () => {
        animate(el, { y: lift }, { type: 'spring', stiffness: 450, damping: 22 });
      });
      el.addEventListener('mouseleave', () => {
        animate(el, { y: 0 }, { type: 'spring', stiffness: 450, damping: 25 });
      });
    });

    // Logo spring hover
    const logoBtn = document.querySelector('.logo-btn');
    if (logoBtn) {
      logoBtn.addEventListener('mouseenter', () => {
        animate(logoBtn, { scale: 1.04 }, { type: 'spring', stiffness: 400, damping: 20 });
      });
      logoBtn.addEventListener('mouseleave', () => {
        animate(logoBtn, { scale: 1.0 }, { type: 'spring', stiffness: 400, damping: 25 });
      });
    }

    // CTA button interactive spring pulse & magnetic cursor track
    const ctaBtn = document.querySelector('.cta-btn');
    if (ctaBtn) {
      ctaBtn.addEventListener('mouseenter', () => {
        animate(ctaBtn, { scale: 1.02, y: -2 }, { type: 'spring', stiffness: 380, damping: 20 });
      });
      ctaBtn.addEventListener('mouseleave', () => {
        animate(ctaBtn, { scale: 1.0, y: 0 }, { type: 'spring', stiffness: 380, damping: 25 });
      });
    }
  }


  // ---------------------------------------------------------------------------
  // The live pulse
  //
  // A judge who never clicks should still see the product working. This runs
  // one real brief on the front page — against the same backend the studio
  // uses — and then puts the answer on trial. It is the same code path, the
  // same cache, and the same Qloo calls, so it costs what the studio costs
  // and nothing more once the brief has been run once.
  // ---------------------------------------------------------------------------
  function initLivePulse() {
    const pulse = document.querySelector('[data-live-pulse]');
    const pulseLabel = pulse ? pulse.querySelector('.live-pulse-label') : null;
    if (!pulse) return;
    const status = pulse.querySelector('[data-pulse-status]');
    const list = pulse.querySelector('[data-pulse-list]');
    const note = pulse.querySelector('[data-pulse-note]');
    // The first prepared brief: the studio offers the same one, and
    // scripts/prewarm.py fetches its evidence before anyone clicks.
    const brief = (demoBriefs.briefs.find((item) => item.id === 'tokyo-morning-bakery') ?? demoBriefs.briefs[0]).project;
    // The card names the brief it actually runs, so its label can never describe another one.
    const briefLine = pulse.querySelector('[data-pulse-brief]');
    if (briefLine) briefLine.textContent = (brief.businessIdea || brief.businessType) + ' · ' + brief.location;

    function fail(message) {
      status.textContent = message || 'The example could not be retrieved. Try again or start your own exploration.';
      note.textContent = 'No substitute evidence is shown. You can edit a brief in the studio or retry when the service is available.';
      const retry = pulse.querySelector('[data-pulse-retry]');
      if (retry) { retry.hidden = false; retry.textContent = 'Try the example again'; }
    }

    async function post(path, body) {
      const response = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'The service could not answer (' + response.status + ').');
      }
      return response.json();
    }

    async function runPulse() {
      pulse.hidden = false;
      const retryButton = pulse.querySelector('[data-pulse-retry]');
      if (retryButton) retryButton.hidden = true;
      status.textContent = 'Retrieving cultural signals and reference places for this brief…';
      note.textContent = 'Held evidence is reused. A fresh lookup can take a minute or two.';
      try {
        const answer = await post('/api/projects/generate', brief);
        const directions = (answer.concepts || []).slice(0, 3);
        if (!directions.length) return fail('This brief did not support any directions. Try another audience or location in the studio.');
        // Say whether this was fresh or held. Both are real Qloo evidence;
        // only one of them cost a request.
        if (pulseLabel) {
          var delivery = answer.delivery || {};
          pulseLabel.innerHTML = '<span class="live-dot"></span> ' +
            (delivery.kind === 'fresh'
              ? 'LIVE EVIDENCE · NEW QLOO LOOKUP'
              : 'HELD EVIDENCE · NO NEW QLOO CALL');
        }
        status.textContent = 'Qloo returned ' + (answer.evidence || []).filter(function (item) {
          return item.kind === 'entity';
        }).length + ' real places. The directions are built from them:';
        list.innerHTML = directions.map(function (concept, index) {
          return '<li><span class="pulse-rank">' + String(index + 1).padStart(2, '0') +
            '</span><span class="pulse-name"></span><span class="pulse-tagline"></span></li>';
        }).join('');
        const names = list.querySelectorAll('.pulse-name');
        const taglines = list.querySelectorAll('.pulse-tagline');
        directions.forEach(function (concept, index) {
          names[index].textContent = concept.name;
          taglines[index].textContent = concept.tagline || '';
        });

        status.textContent = 'Now putting them on trial against the local evidence…';
        // The directions are already on screen. If the test cannot run, they
        // stay, and the note says why — the page never empties itself.
        // Hand over the answer as soon as it exists. If the test cannot run,
        // the studio still gets the exploration it was performed on.
        window.__cultureforgeHandoff = { answer: answer, challenge: null };
        const open = pulse.querySelector('[data-pulse-open]');
        if (open) open.hidden = false;
        let tested = null;
        try {
          tested = await post('/api/projects/challenge', { project: brief });
        } catch (challengeError) {
          note.textContent = 'The evidence test could not run: ' +
            (challengeError && challengeError.message ? challengeError.message : 'the backend did not answer') + '.';
          return;
        }
        const verdicts = tested.directions || [];
        // Join by id, never by position: the directions come back in the order
        // the evidence leaves them in, and the rows were written in the order
        // they arrived.
        const byId = {};
        verdicts.forEach(function (verdict) { byId[verdict.directionId] = verdict; });
        const conceptsById = {};
        directions.forEach(function (concept) { conceptsById[concept.id] = concept; });
        // Show the list in the order the evidence leaves the directions in —
        // the same order the studio shows — and say so only if it moved.
        const order = tested.order && tested.order.length
          ? tested.order
          : directions.map(function (concept) { return concept.id; });
        list.innerHTML = order.map(function (id, index) {
          const concept = conceptsById[id];
          if (!concept) return '';
          const verdict = byId[id];
          const badge = verdict
            ? '<span class="pulse-verdict is-' + verdict.verdict + '">anchor fit: ' + verdict.verdict + '</span>'
            : '';
          return '<li><span class="pulse-rank">' + String(index + 1).padStart(2, '0') +
            '</span><span class="pulse-name"></span><span class="pulse-tagline"></span>' + badge + '</li>';
        }).join('');
        const reorderedNames = list.querySelectorAll('.pulse-name');
        const reorderedTaglines = list.querySelectorAll('.pulse-tagline');
        order.forEach(function (id, index) {
          const concept = conceptsById[id];
          if (!concept || !reorderedNames[index]) return;
          reorderedNames[index].textContent = concept.name;
          reorderedTaglines[index].textContent = concept.tagline || '';
        });
        const contested = verdicts.filter(function (verdict) { return verdict.verdict === 'contested'; });
        // Only claim the order changed if it did.
        const moved = order.length > 1 && order.some(function (id, index) { return id !== directions[index]?.id; });
        note.textContent = contested.length
          ? 'The evidence contested ' + contested.length + ' anchor assumption' +
            (contested.length === 1 ? '' : 's') + (moved ? ', and the order changed.' : '.')
          : 'Tested against the places Qloo returned.';
        // The profile is a stated assumption, never a silent one.
        const profile = tested.profile || {};
        if (profile.demographic) {
          note.textContent += ' Ranked for the “' + profile.demographic + '” profile' +
            (profile.source === 'default' ? ', a default because the brief names no demographic; change it in the studio.' : ', which the brief names.');
        }
        status.textContent = tested.summary || '';
        // Hand the studio the answer and the test that was run on it, so the
        // link below opens what was just shown.
        // The hand-over now carries the test that was run on it, so the link
        // below opens what was just shown.
        window.__cultureforgeHandoff = { answer: answer, challenge: tested };
      } catch (error) {
        fail(String(error && error.message ? error.message : error));
      }
    }

    // A failure offers a way to try again, so the reader is never stranded.
    const retryButton = pulse.querySelector('[data-pulse-retry]');
    if (retryButton) {
      retryButton.addEventListener('click', function (event) {
        event.preventDefault();
        runPulse();
      });
    }

    // Deliberately no timer: loading a page never spends upstream quota.
  }

  // ---------------------------------------------------------------------------
  // Lifecycle Initialization
  // ---------------------------------------------------------------------------
  function init() {
    initStatsObserver();
    initMobileMenu();
    initLandingNavigation();
    initPrototypeJourney();
    initLivePulse();
    initFramerMotionEnhancements();
    initBackgroundVideo();
    initCinematic();

    // In case Motion script was slightly delayed
    if (!window.Motion) {
      const checkMotionTimer = setInterval(() => {
        if (window.Motion) {
          clearInterval(checkMotionTimer);
          initFramerMotionEnhancements();
        }
      }, 50);
      setTimeout(() => clearInterval(checkMotionTimer), 2000);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
