/* App-specific JS — sidebar toggle, tabs */
(function () {
  'use strict';

  function initAppSidebar() {
    var openers = document.querySelectorAll('[data-app-sidebar-open]');
    var closers = document.querySelectorAll('[data-app-sidebar-close]');
    var sidebar = document.querySelector('[data-app-sidebar]');
    var backdrop = document.querySelector('[data-app-sidebar-backdrop]');
    if (!sidebar) return;
    function open() { sidebar.classList.add('is-open'); if (backdrop) backdrop.classList.add('is-open'); }
    function close() { sidebar.classList.remove('is-open'); if (backdrop) backdrop.classList.remove('is-open'); }
    openers.forEach(function (b) { b.addEventListener('click', open); });
    closers.forEach(function (b) { b.addEventListener('click', close); });
    if (backdrop) backdrop.addEventListener('click', close);
  }

  function initP360Tabs() {
    var tabs = document.querySelectorAll('[data-p360-tab]');
    var panels = document.querySelectorAll('[data-p360-panel]');
    if (!tabs.length) return;
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var name = tab.getAttribute('data-p360-tab');
        tabs.forEach(function (t) { t.classList.toggle('is-active', t === tab); });
        panels.forEach(function (p) { p.classList.toggle('is-active', p.getAttribute('data-p360-panel') === name); });
      });
    });
  }

  function init() {
    initAppSidebar();
    initP360Tabs();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
