/**
 * Intelligence Designed To Evolve — Main Script
 * Vanilla JS + Framer Motion (Motion engine) enhancements
 */

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

    document.querySelectorAll('[data-open-studio]').forEach((link) => {
      link.addEventListener('click', openStudio);
    });
    window.addEventListener('cultureforge:show-landing', showLanding);
    if (window.location.hash.startsWith('#workspace')) openStudio();
  }

  // ---------------------------------------------------------------------------
  // 4. Background Video (Safari-safe playback)
  // ---------------------------------------------------------------------------
  function initBackgroundVideo() {
    const video = document.querySelector('.bg-video');
    if (!video) return;

    // Safari checks the muted *property* before it will autoplay, and it has
    // to be set before play() is called - the HTML attribute alone is not
    // enough on every Safari version.
    video.muted = true;
    video.playsInline = true;
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');

    // Safari draws the native play/pause bar over a paused video. The
    // element is hidden until it is genuinely playing, so the bar can never
    // appear; make sure the controls are off in every case.
    video.controls = false;
    video.removeAttribute('controls');
    video.classList.remove('is-playing');

    // Only reveal the video once it is actually rendering frames. Until then
    // the container's poster stands in for it.
    function markPlaying() {
      video.classList.add('is-playing');
    }
    video.addEventListener('playing', markPlaying);
    video.addEventListener('timeupdate', function () {
      if (!video.paused) markPlaying();
    });

    // A decorative background loop should not run for visitors who asked for
    // reduced motion; the .bg fallback colour keeps the page looking right.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      video.removeAttribute('autoplay');
      video.pause();
      return;
    }

    let started = false;
    function attemptPlay() {
      if (started) return;
      const playback = video.play();
      if (playback && typeof playback.catch === 'function') {
        playback
          .then(function () { started = true; })
          .catch(function () { /* autoplay blocked - wait for a user gesture */ });
      } else {
        started = true;
      }
    }

    // Safari rejects play() when the element has not buffered enough yet, so
    // retry as the data arrives.
    video.addEventListener('canplay', attemptPlay);
    video.addEventListener('loadeddata', attemptPlay);
    attemptPlay();

    // If autoplay was refused outright, the first interaction unlocks it.
    const unlockEvents = ['pointerdown', 'touchstart', 'keydown', 'scroll', 'wheel'];
    function unlock() {
      attemptPlay();
      if (started) {
        unlockEvents.forEach(function (type) { window.removeEventListener(type, unlock); });
      }
    }
    unlockEvents.forEach(function (type) {
      window.addEventListener(type, unlock, { passive: true });
    });
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
  // Lifecycle Initialization
  // ---------------------------------------------------------------------------
  function init() {
    initStatsObserver();
    initMobileMenu();
    initLandingNavigation();
    initPrototypeJourney();
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
