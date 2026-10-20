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
    const links = document.querySelectorAll('.nav-link, .mobile-link, .logo-btn[data-nav], .followup-link[data-nav]');
    const views = document.querySelectorAll('[data-landing-view]');
    const followup = document.querySelector('[data-home-followup]');
    const validViews = new Set(Array.from(views, (view) => view.getAttribute('data-landing-view')));

    function showView(name, updateHistory = true) {
      const target = validViews.has(name) ? name : 'home';
      views.forEach((view) => { view.hidden = view.getAttribute('data-landing-view') !== target; });
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

    links.forEach((link) => link.addEventListener('click', (event) => {
      const target = link.getAttribute('data-nav');
      if (!target) return;
      event.preventDefault();
      showView(target);
    }));
    window.addEventListener('popstate', () => showView(location.hash.slice(1), false));
    showView(location.hash.slice(1), false);
  }

  // The redesigned marketing entry remains the first screen; open the existing
  // React prototype for the creation, results, evidence, and scenario journey.
  function initPrototypeJourney() {
    const root = document.getElementById('root');
    const landing = document.querySelector('.page');
    const background = document.querySelector('.bg');
    if (!root || !landing) return;
    let studioLoaded = false;

    function openStudio(event) {
      event?.preventDefault();
      history.replaceState(null, '', '#workspace/create');
      document.body.classList.add('studio-mode');
      document.body.classList.remove('menu-open');
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
    }

    function showLanding() {
      history.replaceState(null, '', window.location.pathname + window.location.search);
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
    }

    document.querySelectorAll('[data-open-studio]').forEach((link) => {
      link.addEventListener('click', openStudio);
    });
    window.addEventListener('cultureforge:show-landing', showLanding);
    if (window.location.hash.startsWith('#workspace')) openStudio();
  }

  // ---------------------------------------------------------------------------
  // 4. Framer Motion / Motion Spring & Micro-Interactions
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
