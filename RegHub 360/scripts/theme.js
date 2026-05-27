/* RegHub 360 — theme + interactions
   Tiny, no-deps. Loaded with `defer`. */
(function () {
  'use strict';

  // ---------- Theme ----------
  var STORAGE_KEY = 'reghub.theme';
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
  }
  // Set ASAP via inline script in <head>, but also init here for buttons
  function initThemeToggles() {
    var toggles = document.querySelectorAll('[data-theme-toggle]');
    toggles.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme') || 'light';
        applyTheme(current === 'light' ? 'dark' : 'light');
      });
    });
  }

  // ---------- Mobile nav ----------
  function initMobileNav() {
    var openers = document.querySelectorAll('[data-mobile-nav-open]');
    var closers = document.querySelectorAll('[data-mobile-nav-close]');
    var nav = document.querySelector('[data-mobile-nav]');
    if (!nav) return;
    openers.forEach(function (b) { b.addEventListener('click', function () { nav.classList.add('is-open'); document.body.style.overflow = 'hidden'; }); });
    closers.forEach(function (b) { b.addEventListener('click', function () { nav.classList.remove('is-open'); document.body.style.overflow = ''; }); });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('is-open'); document.body.style.overflow = ''; });
    });
  }

  // ---------- Reveal on scroll ----------
  function initReveal() {
    if (typeof IntersectionObserver === 'undefined') return;
    var els = document.querySelectorAll('[data-reveal]');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  // ---------- Use case tabs ----------
  function initTabs() {
    document.querySelectorAll('[data-tabs]').forEach(function (root) {
      var buttons = root.querySelectorAll('[data-tab]');
      var panels = root.querySelectorAll('[data-panel]');
      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          var name = btn.getAttribute('data-tab');
          buttons.forEach(function (b) { b.classList.toggle('is-active', b === btn); });
          panels.forEach(function (p) { p.classList.toggle('is-active', p.getAttribute('data-panel') === name); });
        });
      });
    });
  }

  // ---------- Live demo search ----------
  function initLiveDemo() {
    var input = document.querySelector('[data-demo-input]');
    var results = document.querySelector('[data-demo-results]');
    var chips = document.querySelectorAll('[data-demo-chip]');
    if (!input || !results) return;

    var DATA = {
      '광동제약':  { kind: '업체', drug: 312, recall: 4, sanction: 2, safety: 1, supply: 0, food: 87 },
      '베니톨정':  { kind: '의약품', drug: 1, recall: 0, sanction: 0, safety: 1, supply: 0, food: 0, synonym: '아세트아미노펜 500mg' },
      '비타500':   { kind: '식품', drug: 0, recall: 0, sanction: 1, safety: 0, supply: 0, food: 1, synonym: '혼합음료 · 광동제약' },
      '아세트아미노펜': { kind: '성분', drug: 312, recall: 3, sanction: 0, safety: 1, supply: 0, food: 0 },
      '광동':  { kind: '업체', drug: 312, recall: 4, sanction: 2, safety: 1, supply: 0, food: 87 }
    };

    function render(query) {
      var key = (query || '').trim();
      if (!key) {
        results.removeAttribute('data-state');
        return;
      }
      // fuzzy: pick a known key that starts with query
      var match = null;
      var keys = Object.keys(DATA);
      for (var i = 0; i < keys.length; i++) {
        if (keys[i].indexOf(key) === 0) { match = keys[i]; break; }
      }
      if (!match) {
        for (var j = 0; j < keys.length; j++) {
          if (keys[j].indexOf(key) !== -1) { match = keys[j]; break; }
        }
      }
      var d = match ? DATA[match] : null;
      if (!d) {
        results.setAttribute('data-state', 'empty');
        results.querySelector('[data-result-title]').textContent = key;
        results.querySelector('[data-result-kind]').textContent = '— 결과 없음';
        results.querySelectorAll('[data-result-stat]').forEach(function (el) { el.textContent = '0'; });
        return;
      }
      results.setAttribute('data-state', 'loaded');
      results.querySelector('[data-result-title]').textContent = match;
      results.querySelector('[data-result-kind]').textContent = d.kind + (d.synonym ? ' · ' + d.synonym : '');
      var stats = ['drug','recall','sanction','safety','supply','food'];
      stats.forEach(function (k) {
        var el = results.querySelector('[data-result-stat="' + k + '"]');
        if (el) el.textContent = d[k];
      });
    }

    input.addEventListener('input', function () { render(input.value); });
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        input.value = c.getAttribute('data-demo-chip');
        render(input.value);
        input.focus();
      });
    });
    // Initial state
    render(input.value);
  }

  function init() {
    initThemeToggles();
    initMobileNav();
    initReveal();
    initTabs();
    initLiveDemo();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
