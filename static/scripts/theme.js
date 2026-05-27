/* RegHub 360 — theme + interactions
   Tiny, no-deps. Loaded with `defer`. */
(function () {
  'use strict';

  // ---------- Theme (light / dark / auto 3단계) ----------
  var STORAGE_KEY = 'reghub.theme';
  var MQ_DARK = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function getStoredPreference() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }
  function setStoredPreference(value) {
    try { localStorage.setItem(STORAGE_KEY, value); } catch (e) {}
  }
  function resolveTheme(pref) {
    // pref ∈ {'light','dark','auto',null}. auto / null → 시스템 우선
    if (pref === 'light' || pref === 'dark') return pref;
    return (MQ_DARK && MQ_DARK.matches) ? 'dark' : 'light';
  }
  function applyTheme(pref) {
    var resolved = resolveTheme(pref);
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.setAttribute('data-theme-pref', pref || 'auto');
    setStoredPreference(pref || 'auto');
  }
  function nextPref(current) {
    // light → dark → auto → light ...
    if (current === 'light') return 'dark';
    if (current === 'dark') return 'auto';
    return 'light';
  }
  function initThemeToggles() {
    var toggles = document.querySelectorAll('[data-theme-toggle]');
    toggles.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme-pref') || getStoredPreference() || 'auto';
        applyTheme(nextPref(current));
      });
    });
    // 시스템 모드 변경 시 auto 모드면 따라감
    if (MQ_DARK && MQ_DARK.addEventListener) {
      MQ_DARK.addEventListener('change', function () {
        var pref = document.documentElement.getAttribute('data-theme-pref') || 'auto';
        if (pref === 'auto') applyTheme('auto');
      });
    }
    // 첫 진입 시 저장된 preference 반영 (head inline script가 light/dark만 적용했으므로 auto 상태도 명시)
    var stored = getStoredPreference();
    if (!stored || stored === 'auto') {
      applyTheme('auto');
    } else {
      applyTheme(stored);
    }
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

  // ---------- Live demo search (실 API 연동 — /api/landing-demo) ----------
  function initLiveDemo() {
    var input = document.querySelector('[data-demo-input]');
    var results = document.querySelector('[data-demo-results]');
    var chips = document.querySelectorAll('[data-demo-chip]');
    if (!input || !results) return;

    var debounceTimer = null;
    var lastQuery = null;
    var STAT_KEYS = ['drug', 'recall', 'sanction', 'safety', 'supply', 'food'];

    function setLoading(query) {
      results.setAttribute('data-state', 'loading');
      var titleEl = results.querySelector('[data-result-title]');
      var kindEl = results.querySelector('[data-result-kind]');
      if (titleEl) titleEl.textContent = query;
      if (kindEl) kindEl.textContent = '— 조회 중...';
      STAT_KEYS.forEach(function (k) {
        var el = results.querySelector('[data-result-stat="' + k + '"]');
        if (el) el.textContent = '…';
      });
    }

    function setResult(query, data) {
      var titleEl = results.querySelector('[data-result-title]');
      var kindEl = results.querySelector('[data-result-kind]');
      if (titleEl) titleEl.textContent = query;

      if (!data || !data.success) {
        results.setAttribute('data-state', 'empty');
        if (kindEl) kindEl.textContent = '— ' + (data && data.error || '결과 없음');
        STAT_KEYS.forEach(function (k) {
          var el = results.querySelector('[data-result-stat="' + k + '"]');
          if (el) el.textContent = '0';
        });
        return;
      }

      results.setAttribute('data-state', 'loaded');
      var meta = (data.kind || '검색') + ' · ' + (data.cached ? '캐시' : '실 API');
      if (kindEl) kindEl.textContent = meta;

      var counts = data.counts || {};
      STAT_KEYS.forEach(function (k) {
        var el = results.querySelector('[data-result-stat="' + k + '"]');
        if (el) el.textContent = counts[k] != null ? counts[k] : 0;
      });
    }

    function fetchDemo(query) {
      var key = (query || '').trim();
      if (!key) {
        results.removeAttribute('data-state');
        return;
      }
      if (key === lastQuery) return;
      lastQuery = key;
      setLoading(key);

      fetch('/api/landing-demo?q=' + encodeURIComponent(key), {
        headers: { 'Accept': 'application/json' }
      })
        .then(function (r) { return r.json(); })
        .then(function (data) { setResult(key, data); })
        .catch(function (err) {
          console.error('Live demo fetch 실패:', err);
          setResult(key, { success: false, error: '네트워크 오류' });
        });
    }

    // 입력 시 300ms 디바운스
    input.addEventListener('input', function () {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () { fetchDemo(input.value); }, 300);
    });

    // 칩 클릭 → 즉시 조회
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        input.value = c.getAttribute('data-demo-chip');
        fetchDemo(input.value);
        input.focus();
      });
    });

    // 초기값 (placeholder의 '광동제약')
    if (input.value) fetchDemo(input.value);
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
