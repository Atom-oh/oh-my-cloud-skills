/**
 * Reactive Presentation shared overlay core.
 * Optional navigation and detail modules register before framework initialization.
 */
(function() {
  'use strict';

  let framework = null;
  let deck = null;
  let uiScale = 1;
  let suppressedFocusTerm = null;
  const modules = {};
  const overlayRoots = [];
  const navigationKeys = new Set([
    'ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown', ' ',
    'PageUp', 'PageDown', 'Home', 'End'
  ]);

  function call(name, method, ...args) {
    const module = modules[name];
    if (module && module[method]) return module[method](...args);
  }

  function registeredModules() {
    return Object.values(modules).sort((a, b) => a.priority - b.priority);
  }

  function register(name, module) {
    modules[name] = module;
  }

  function isTypingTarget(target) {
    if (!target) return false;
    const tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
      target.isContentEditable;
  }

  function isOverview() {
    return Boolean(deck && deck.classList.contains('overview-mode'));
  }

  function liveTerm(target) {
    const term = target && target.closest ? target.closest('.rp-detail') : null;
    if (!term || !deck || !deck.contains(term)) return null;
    const slide = term.closest('.slide');
    return slide && slide.parentElement === deck ? term : null;
  }

  function normalizeText(value) {
    return String(value || '').replace(/\s+/g, ' ').trim();
  }

  function restoreFocusWithoutTooltip(target) {
    if (!target || !target.isConnected || !target.focus) return;
    suppressedFocusTerm = liveTerm(target);
    target.focus();
    suppressedFocusTerm = null;
  }

  function makeOverlay(tag, id) {
    const el = document.createElement(tag);
    el.id = id;
    el.className = 'rp-overlay-ui';
    if (document.documentElement.lang) el.lang = document.documentElement.lang;
    document.body.appendChild(el);
    overlayRoots.push(el);
    return el;
  }

  function updateOverlayScale() {
    if (!deck) return;
    const rawScale = parseFloat(getComputedStyle(deck).getPropertyValue('--deck-scale'));
    uiScale = Number.isFinite(rawScale) && rawScale > 0 ? rawScale : 1;
    const rootFont = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    document.documentElement.style.setProperty('--rp-ui-scale', String(uiScale));
    document.documentElement.style.setProperty('--rp-ui-rem', (rootFont * uiScale) + 'px');
  }

  function applyOverlayTheme() {
    if (!deck) return;
    const active = deck.querySelector(':scope > .slide.active') ||
      deck.children[framework ? framework.currentSlide : 0];
    const deckDark = deck.classList.contains('theme-dark');
    const dark = active && (active.classList.contains('theme-dark') ||
      (deckDark && !active.classList.contains('theme-light')));
    overlayRoots.forEach(root => {
      root.classList.toggle('theme-dark', Boolean(dark));
      root.classList.toggle('theme-light', !dark);
    });
  }

  function handleGlobalKeydown(event) {
    if (event.isComposing || event.keyCode === 229) return;
    if (navigationKeys.has(event.key)) call('detail', 'hideTooltip');
    registeredModules().some(module => module.keydown && module.keydown(event));
  }

  function init(instance) {
    if (framework) return;
    framework = instance;
    deck = document.querySelector('.slide-deck');
    if (!deck) return;

    registeredModules().forEach(module => module.init(instance, deck));
    updateOverlayScale();
    document.addEventListener('keydown', handleGlobalKeydown);
    document.addEventListener('rp:slidechange', () => {
      registeredModules().forEach(module => {
        if (module.slideChange) module.slideChange();
      });
      applyOverlayTheme();
    });
    const stateObserver = new MutationObserver(records => {
      let termsChanged = false;
      let scaleChanged = false;
      records.forEach(record => {
        if (record.attributeName === 'class') termsChanged = true;
        if (record.target === deck && record.attributeName === 'style') scaleChanged = true;
      });
      if (scaleChanged) updateOverlayScale();
      if (termsChanged) {
        call('detail', 'updateAllTermStates');
        if (isOverview()) {
          call('nav', 'closeAgenda');
          call('nav', 'closeSearch');
          call('detail', 'closeDetail', false);
          call('detail', 'hideTooltip');
        }
      }
    });
    stateObserver.observe(deck, {
      attributes: true,
      attributeFilter: ['class', 'style'],
      subtree: true
    });
    window.addEventListener('resize', () => requestAnimationFrame(updateOverlayScale));
    document.addEventListener('fullscreenchange', () => requestAnimationFrame(updateOverlayScale));
    requestAnimationFrame(updateOverlayScale);
    applyOverlayTheme();
  }

  window.DeckOverlay = {
    init: init,
    register: register,
    openSearch: (...args) => call('nav', 'openSearch', ...args),
    closeSearch: (...args) => call('nav', 'closeSearch', ...args),
    openDetail: (...args) => call('detail', 'openDetail', ...args),
    closeDetail: (...args) => call('detail', 'closeDetail', ...args),
    buildIndex: () => call('nav', 'buildIndex') || [],
    detailOpener: () => call('detail', 'detailOpener') || null,
    blockAgendaUnderPointer: () => call('nav', 'blockAgendaUnderPointer'),
    normalizeText: normalizeText,
    liveTerm: liveTerm,
    isOverview: isOverview,
    isTypingTarget: isTypingTarget,
    navigationKeys: navigationKeys,
    makeOverlay: makeOverlay,
    uiScale: () => uiScale,
    restoreFocusWithoutTooltip: restoreFocusWithoutTooltip,
    isSuppressedFocusTerm: term => term === suppressedFocusTerm
  };
})();
