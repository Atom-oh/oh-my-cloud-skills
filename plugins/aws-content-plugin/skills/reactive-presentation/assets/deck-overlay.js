/**
 * Reactive Presentation deck overlays.
 * Agenda, search, tooltips, and detail panels stay outside slide content.
 */
(function() {
  'use strict';

  let framework = null;
  let deck = null;
  let searchIndex = [];
  let agendaCloseTimer = null;
  let selectedResult = 0;
  let previousFocus = null;
  let touchTerm = null;
  let tooltipTerm = null;
  let detailOpener = null;
  let uiScale = 1;
  let ignoreMouseUntil = 0;
  let agendaHotzoneBlocked = false;
  let pointerX = null;
  let pointerY = null;
  let suppressedFocusTerm = null;

  const overlayRoots = [];
  const navigationKeys = new Set([
    'ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown', ' ',
    'PageUp', 'PageDown', 'Home', 'End'
  ]);

  function isTypingTarget(target) {
    if (!target) return false;
    const tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
      target.isContentEditable;
  }

  function isOverview() {
    return Boolean(deck && deck.classList.contains('overview-mode'));
  }

  function pointerIsInAgendaHotzone() {
    const hotzone = document.getElementById('rp-agenda-hotzone');
    if (!hotzone || pointerX === null || pointerY === null) return false;
    const rect = hotzone.getBoundingClientRect();
    return pointerX >= rect.left && pointerX <= rect.right &&
      pointerY >= rect.top && pointerY <= rect.bottom;
  }

  function blockAgendaUnderPointer() {
    agendaHotzoneBlocked = pointerIsInAgendaHotzone();
  }

  function restoreFocusWithoutTooltip(target) {
    if (!target || !target.isConnected || !target.focus) return;
    suppressedFocusTerm = liveTerm(target);
    target.focus();
    suppressedFocusTerm = null;
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

  function slideTitle(slide, index) {
    const heading = slide.querySelector('h1, h2');
    return normalizeText(heading ? heading.textContent : '') || 'Slide ' + (index + 1);
  }

  function visibleSlideText(slide) {
    const values = [];
    const heading = slide.querySelector('h1, h2');
    const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT, {
      acceptNode: node => {
        const parent = node.parentElement;
        if (!parent || !normalizeText(node.nodeValue)) return NodeFilter.FILTER_REJECT;
        if (heading && heading.contains(parent)) return NodeFilter.FILTER_REJECT;
        if (parent.closest('style, script, template, .rp-detail-store')) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    while (walker.nextNode()) values.push(walker.currentNode.nodeValue);
    return normalizeText(values.join(' '));
  }

  function detailSlideText(slide) {
    const values = [];
    slide.querySelectorAll('.rp-detail-store section').forEach(section => {
      values.push(section.dataset.title || '');
      values.push(section.dataset.text || section.textContent || '');
    });
    slide.querySelectorAll('.rp-detail[data-tip]').forEach(term => {
      values.push(term.dataset.tip || '');
    });
    return normalizeText(values.join(' '));
  }

  function buildIndex() {
    const slides = Array.from(document.querySelectorAll('.slide-deck > .slide'));
    searchIndex = slides.map((slide, index) => ({
      index: index,
      block: slide.dataset.block || '__deck__',
      blockTitle: normalizeText(slide.dataset.blockTitle) || document.title,
      title: slideTitle(slide, index),
      text: visibleSlideText(slide),
      detailText: detailSlideText(slide)
    }));
    return searchIndex;
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

  function termIsAvailable(term) {
    return Boolean(term && liveTerm(term) && !isOverview() &&
      !term.closest('.fragment:not(.visible)'));
  }

  function updateTermState(term) {
    const available = termIsAvailable(term);
    term.setAttribute('tabindex', available ? '0' : '-1');
    if (term.dataset.detail) {
      term.setAttribute('role', 'button');
      term.setAttribute('aria-haspopup', 'dialog');
      term.setAttribute('aria-controls', 'rp-detail-panel');
      if (!term.hasAttribute('aria-expanded')) term.setAttribute('aria-expanded', 'false');
    }
    if (!available && tooltipTerm === term) hideTooltip();
    if (!available && detailOpener === term) closeDetail(false);
  }

  function updateAllTermStates() {
    if (!deck) return;
    deck.querySelectorAll(':scope > .slide .rp-detail').forEach(updateTermState);
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

  function createAgenda() {
    const hotzone = makeOverlay('div', 'rp-agenda-hotzone');
    hotzone.setAttribute('aria-label', 'Open agenda');

    const agenda = makeOverlay('nav', 'rp-agenda');
    agenda.setAttribute('aria-label', 'Slide agenda');

    const groups = [];
    searchIndex.forEach(item => {
      let group = groups[groups.length - 1];
      if (!group || group.key !== item.block) {
        group = { key: item.block, title: item.blockTitle, slides: [] };
        groups.push(group);
      }
      group.slides.push(item);
    });

    groups.forEach(group => {
      const block = document.createElement('section');
      block.className = 'rp-agenda-block';

      const header = document.createElement('button');
      header.type = 'button';
      header.className = 'rp-agenda-block-title';
      header.dataset.goto = group.slides[0].index;
      header.textContent = group.title;
      block.appendChild(header);

      const rows = document.createElement('div');
      rows.className = 'rp-agenda-slides';
      group.slides.forEach(item => {
        const row = document.createElement('button');
        row.type = 'button';
        row.className = 'rp-agenda-row';
        row.dataset.goto = item.index;

        const number = document.createElement('span');
        number.className = 'rp-agenda-number';
        number.textContent = String(item.index + 1);
        const title = document.createElement('span');
        title.className = 'rp-agenda-title';
        title.textContent = item.title;
        row.append(number, title);
        rows.appendChild(row);
      });
      block.appendChild(rows);
      agenda.appendChild(block);
    });

    const open = () => {
      if (agendaHotzoneBlocked || isOverview() ||
          document.body.classList.contains('rp-detail-open') ||
          document.body.classList.contains('rp-search-open')) return;
      clearTimeout(agendaCloseTimer);
      updateAgenda();
      document.body.classList.add('rp-agenda-open');
    };
    const scheduleClose = () => {
      clearTimeout(agendaCloseTimer);
      agendaCloseTimer = setTimeout(closeAgenda, 300);
    };

    hotzone.addEventListener('mouseenter', open);
    hotzone.addEventListener('mouseleave', () => {
      agendaHotzoneBlocked = false;
      scheduleClose();
    });
    agenda.addEventListener('mouseenter', () => clearTimeout(agendaCloseTimer));
    agenda.addEventListener('mouseleave', scheduleClose);
    agenda.addEventListener('click', event => {
      const target = event.target.closest('[data-goto]');
      if (!target) return;
      closeAgenda();
      framework.goTo(Number(target.dataset.goto));
    });
  }

  function closeAgenda() {
    clearTimeout(agendaCloseTimer);
    document.body.classList.remove('rp-agenda-open');
  }

  function updateAgenda() {
    const agenda = document.getElementById('rp-agenda');
    if (!agenda || !framework) return;
    agenda.querySelectorAll('.rp-agenda-row').forEach(row => {
      row.classList.toggle('is-current', Number(row.dataset.goto) === framework.currentSlide);
    });
    agenda.querySelectorAll('.rp-agenda-block').forEach(block => {
      block.classList.toggle('is-current-block',
        Boolean(block.querySelector('.rp-agenda-row.is-current')));
    });
  }

  function appendHighlightedText(container, text, query) {
    const source = normalizeText(text);
    const lower = source.toLocaleLowerCase();
    const needle = query.toLocaleLowerCase();
    const matchAt = lower.indexOf(needle);
    if (matchAt < 0) {
      container.textContent = source;
      return;
    }

    const start = Math.max(0, matchAt - 42);
    const end = Math.min(source.length, matchAt + query.length + 68);
    if (start > 0) container.appendChild(document.createTextNode('...'));
    container.appendChild(document.createTextNode(source.slice(start, matchAt)));
    const mark = document.createElement('mark');
    mark.textContent = source.slice(matchAt, matchAt + query.length);
    container.appendChild(mark);
    container.appendChild(document.createTextNode(source.slice(matchAt + query.length, end)));
    if (end < source.length) container.appendChild(document.createTextNode('...'));
  }

  function matchingResults(query) {
    const needle = query.toLocaleLowerCase();
    return searchIndex.map(item => {
      const titleHit = item.title.toLocaleLowerCase().includes(needle);
      const textHit = item.text.toLocaleLowerCase().includes(needle);
      const detailHit = item.detailText.toLocaleLowerCase().includes(needle);
      if (!titleHit && !textHit && !detailHit) return null;
      return {
        item: item,
        rank: titleHit ? 0 : (textHit ? 1 : 2),
        source: titleHit ? item.title : (textHit ? item.text : item.detailText)
      };
    }).filter(Boolean).sort((a, b) =>
      a.rank - b.rank || a.item.index - b.item.index
    ).slice(0, 20);
  }

  function updateSearchSelection(index, scroll = true) {
    const rows = Array.from(document.querySelectorAll('#rp-search-results .rp-search-row'));
    const input = document.getElementById('rp-search-input');
    if (!rows.length) {
      selectedResult = 0;
      if (input) input.removeAttribute('aria-activedescendant');
      return;
    }

    selectedResult = Math.max(0, Math.min(index, rows.length - 1));
    rows.forEach((row, rowIndex) => {
      const selected = rowIndex === selectedResult;
      row.classList.toggle('is-selected', selected);
      row.setAttribute('aria-selected', selected ? 'true' : 'false');
    });
    if (input) input.setAttribute('aria-activedescendant', rows[selectedResult].id);
    if (scroll) rows[selectedResult].scrollIntoView({ block: 'nearest' });
  }

  function renderSearch() {
    const input = document.getElementById('rp-search-input');
    const resultsEl = document.getElementById('rp-search-results');
    if (!input || !resultsEl) return;
    const query = input.value.trim();
    resultsEl.replaceChildren();
    selectedResult = 0;
    if (!query) {
      input.removeAttribute('aria-activedescendant');
      return;
    }

    const results = matchingResults(query);
    results.forEach((result, index) => {
      const row = document.createElement('button');
      row.type = 'button';
      row.className = 'rp-search-row';
      row.id = 'rp-search-option-' + result.item.index;
      row.dataset.goto = result.item.index;
      row.setAttribute('role', 'option');
      row.setAttribute('aria-selected', 'false');
      row.tabIndex = -1;

      const meta = document.createElement('span');
      meta.className = 'rp-search-meta';
      meta.textContent = result.item.blockTitle + ' / ' + (result.item.index + 1);
      const title = document.createElement('strong');
      title.className = 'rp-search-title';
      title.textContent = result.item.title;
      const separator = document.createElement('span');
      separator.className = 'rp-search-separator';
      separator.textContent = '. ';
      separator.style.position = 'absolute';
      separator.style.width = '1px';
      separator.style.height = '1px';
      separator.style.padding = '0';
      separator.style.margin = '-1px';
      separator.style.overflow = 'hidden';
      separator.style.clipPath = 'inset(50%)';
      separator.style.whiteSpace = 'nowrap';
      separator.style.border = '0';
      const snippet = document.createElement('span');
      snippet.className = 'rp-search-snippet';
      appendHighlightedText(snippet, result.source, query);
      row.append(meta, title, separator, snippet);
      resultsEl.appendChild(row);
    });
    updateSearchSelection(0, false);
  }

  function moveSearchSelection(delta) {
    const rows = Array.from(document.querySelectorAll('#rp-search-results .rp-search-row'));
    if (!rows.length) return;
    updateSearchSelection((selectedResult + delta + rows.length) % rows.length);
  }

  function activateSearchSelection() {
    const rows = document.querySelectorAll('#rp-search-results .rp-search-row');
    const row = rows[selectedResult];
    if (!row) return;
    const index = Number(row.dataset.goto);
    closeSearch(false);
    framework.goTo(index);
  }

  function createSearch() {
    const root = makeOverlay('div', 'rp-search');
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-label', 'Search slides');

    const dialog = document.createElement('div');
    dialog.className = 'rp-search-dialog';
    const input = document.createElement('input');
    input.id = 'rp-search-input';
    input.type = 'search';
    input.autocomplete = 'off';
    input.placeholder = 'Search slides';
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-controls', 'rp-search-results');
    input.setAttribute('aria-autocomplete', 'list');
    const results = document.createElement('div');
    results.id = 'rp-search-results';
    results.setAttribute('role', 'listbox');
    dialog.append(input, results);
    root.appendChild(dialog);

    input.addEventListener('input', renderSearch);
    results.addEventListener('mouseover', event => {
      const row = event.target.closest('.rp-search-row');
      if (!row) return;
      const rows = Array.from(results.querySelectorAll('.rp-search-row'));
      updateSearchSelection(rows.indexOf(row), false);
    });
    results.addEventListener('click', event => {
      const row = event.target.closest('.rp-search-row');
      if (!row) return;
      closeSearch(false);
      framework.goTo(Number(row.dataset.goto));
    });
    root.addEventListener('pointerdown', event => {
      if (event.target === root) closeSearch();
    });
  }

  function openSearch() {
    if (isOverview()) return;
    const input = document.getElementById('rp-search-input');
    if (!input) return;
    previousFocus = document.body.classList.contains('rp-detail-open') &&
      termIsAvailable(detailOpener) ? detailOpener : document.activeElement;
    closeAgenda();
    closeDetail(false);
    document.body.classList.add('rp-search-open');
    input.setAttribute('aria-expanded', 'true');
    input.value = '';
    renderSearch();
    input.focus();
  }

  function closeSearch(restoreFocus = true) {
    if (!document.body.classList.contains('rp-search-open')) return;
    document.body.classList.remove('rp-search-open');
    const input = document.getElementById('rp-search-input');
    if (input) {
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
    }
    blockAgendaUnderPointer();
    if (restoreFocus) restoreFocusWithoutTooltip(previousFocus);
    previousFocus = null;
  }

  function createTooltip() {
    const tooltip = makeOverlay('div', 'rp-tooltip');
    tooltip.setAttribute('role', 'tooltip');
    tooltip.setAttribute('aria-hidden', 'true');
  }

  function showTooltip(term) {
    const tooltip = document.getElementById('rp-tooltip');
    const tip = term && term.dataset.tip;
    if (!tooltip || !tip || !termIsAvailable(term)) return;
    if (tooltipTerm && tooltipTerm !== term) {
      const ids = (tooltipTerm.getAttribute('aria-describedby') || '')
        .split(/\s+/).filter(id => id && id !== tooltip.id);
      if (ids.length) tooltipTerm.setAttribute('aria-describedby', ids.join(' '));
      else tooltipTerm.removeAttribute('aria-describedby');
    }
    tooltipTerm = term;
    const describedBy = new Set(
      (term.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean)
    );
    describedBy.add(tooltip.id);
    term.setAttribute('aria-describedby', Array.from(describedBy).join(' '));
    tooltip.textContent = tip;
    tooltip.setAttribute('aria-hidden', 'false');
    tooltip.classList.add('is-visible');

    const anchor = term.getBoundingClientRect();
    const box = tooltip.getBoundingClientRect();
    const gap = 12 * uiScale;
    const left = Math.max(gap, Math.min(
      anchor.left + anchor.width / 2 - box.width / 2,
      window.innerWidth - box.width - gap
    ));
    let top = anchor.top - box.height - gap;
    if (top < gap) top = anchor.bottom + gap;
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
  }

  function hideTooltip() {
    const tooltip = document.getElementById('rp-tooltip');
    if (!tooltip) return;
    if (tooltipTerm) {
      const ids = (tooltipTerm.getAttribute('aria-describedby') || '')
        .split(/\s+/).filter(id => id && id !== tooltip.id);
      if (ids.length) tooltipTerm.setAttribute('aria-describedby', ids.join(' '));
      else tooltipTerm.removeAttribute('aria-describedby');
    }
    tooltipTerm = null;
    tooltip.classList.remove('is-visible');
    tooltip.setAttribute('aria-hidden', 'true');
    touchTerm = null;
  }

  function createDetailPanel() {
    const panel = makeOverlay('aside', 'rp-detail-panel');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'false');
    panel.setAttribute('tabindex', '-1');

    const header = document.createElement('header');
    header.className = 'rp-detail-header';
    const title = document.createElement('h2');
    title.className = 'rp-detail-title';
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'rp-detail-close';
    close.setAttribute('aria-label', 'Close details');
    close.textContent = 'Close';
    header.append(title, close);

    const body = document.createElement('div');
    body.className = 'rp-detail-body';
    panel.append(header, body);
    close.addEventListener('click', closeDetail);
  }

  function openDetail(slideEl, id, opener) {
    if (!slideEl || !id) return;
    const activeTerm = liveTerm(document.activeElement);
    const candidate = opener ||
      (activeTerm && activeTerm.dataset.detail === String(id) ? activeTerm : null) ||
      Array.from(slideEl.querySelectorAll('.rp-detail[data-detail]'))
        .find(term => term.dataset.detail === String(id));
    if (!termIsAvailable(candidate)) return;
    const section = Array.from(
      slideEl.querySelectorAll('.rp-detail-store section[data-detail-id]')
    ).find(el => el.dataset.detailId === String(id));
    if (!section) return;

    const panel = document.getElementById('rp-detail-panel');
    const title = panel.querySelector('.rp-detail-title');
    const body = panel.querySelector('.rp-detail-body');
    title.textContent = section.dataset.title || '';
    body.replaceChildren(...Array.from(section.childNodes, node => node.cloneNode(true)));
    panel.setAttribute('aria-label', title.textContent || 'Slide details');
    deck.querySelectorAll(':scope > .slide .rp-detail[data-detail]').forEach(term => {
      term.setAttribute('aria-expanded', term === candidate ? 'true' : 'false');
    });
    detailOpener = candidate;
    document.body.classList.add('rp-detail-open');
    hideTooltip();
    const close = panel.querySelector('.rp-detail-close');
    setTimeout(() => {
      if (document.body.classList.contains('rp-detail-open')) (close || panel).focus();
    }, 50);
  }

  function closeDetail(restoreFocus = true) {
    const wasOpen = document.body.classList.contains('rp-detail-open');
    document.body.classList.remove('rp-detail-open');
    if (deck) {
      deck.querySelectorAll(':scope > .slide .rp-detail[data-detail]')
        .forEach(term => term.setAttribute('aria-expanded', 'false'));
    }
    const opener = detailOpener;
    detailOpener = null;
    if (wasOpen) blockAgendaUnderPointer();
    if (wasOpen && restoreFocus && termIsAvailable(opener)) {
      restoreFocusWithoutTooltip(opener);
    }
  }

  function bindDetailEvents() {
    deck.addEventListener('mouseover', event => {
      if (Date.now() < ignoreMouseUntil) return;
      const term = liveTerm(event.target);
      if (termIsAvailable(term)) showTooltip(term);
    });
    deck.addEventListener('mouseout', event => {
      const term = liveTerm(event.target);
      if (!term || term.contains(event.relatedTarget)) return;
      hideTooltip();
    });
    deck.addEventListener('focusin', event => {
      const term = liveTerm(event.target);
      if (term && term === suppressedFocusTerm) {
        hideTooltip();
        return;
      }
      if (termIsAvailable(term)) showTooltip(term);
    });
    deck.addEventListener('focusout', event => {
      const term = liveTerm(event.target);
      if (!term || term.contains(event.relatedTarget)) return;
      hideTooltip();
    });
    deck.addEventListener('pointerdown', event => {
      const term = liveTerm(event.target);
      if (!termIsAvailable(term) || term.dataset.detail || event.pointerType !== 'touch') return;
      ignoreMouseUntil = Date.now() + 500;
      if (touchTerm === term && document.getElementById('rp-tooltip').classList.contains('is-visible')) {
        hideTooltip();
      } else {
        touchTerm = term;
        showTooltip(term);
        touchTerm = term;
      }
    });
    deck.addEventListener('click', event => {
      const term = liveTerm(event.target);
      if (!termIsAvailable(term) || !term.dataset.detail) return;
      openDetail(term.closest('.slide'), term.dataset.detail, term);
    });
    deck.addEventListener('keydown', event => {
      const term = liveTerm(event.target);
      if (!termIsAvailable(term) || !term.dataset.detail || event.key !== 'Enter') return;
      event.preventDefault();
      openDetail(term.closest('.slide'), term.dataset.detail, term);
    });

    document.addEventListener('pointerdown', event => {
      if (!document.body.classList.contains('rp-detail-open')) return;
      const panel = document.getElementById('rp-detail-panel');
      if (!panel.contains(event.target) && !liveTerm(event.target)) closeDetail();
    });
  }

  function handleGlobalKeydown(event) {
    if (event.isComposing || event.keyCode === 229) return;
    if (navigationKeys.has(event.key)) hideTooltip();

    if (document.body.classList.contains('rp-search-open')) {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopImmediatePropagation();
        closeSearch();
      } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        moveSearchSelection(1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        moveSearchSelection(-1);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        activateSearchSelection();
      }
      return;
    }

    if (document.body.classList.contains('rp-detail-open')) {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopImmediatePropagation();
        closeDetail();
        return;
      }
      if (navigationKeys.has(event.key)) {
        closeDetail();
      }
    }

    if (isTypingTarget(event.target) || isOverview()) return;
    const searchShortcut = (event.metaKey || event.ctrlKey) &&
      event.key.toLocaleLowerCase() === 'k';
    if (searchShortcut || event.key === '/') {
      event.preventDefault();
      openSearch();
    }
  }

  function init(instance) {
    if (framework) return;
    framework = instance;
    deck = document.querySelector('.slide-deck');
    if (!deck) return;

    buildIndex();
    document.querySelectorAll('.slide-sidebar .rp-detail').forEach(term => {
      term.setAttribute('tabindex', '-1');
    });

    createAgenda();
    createSearch();
    createTooltip();
    createDetailPanel();
    updateAllTermStates();
    updateOverlayScale();
    bindDetailEvents();
    document.addEventListener('pointermove', event => {
      pointerX = event.clientX;
      pointerY = event.clientY;
      if (agendaHotzoneBlocked && !pointerIsInAgendaHotzone()) {
        agendaHotzoneBlocked = false;
      }
    });
    document.addEventListener('pointerdown', event => {
      pointerX = event.clientX;
      pointerY = event.clientY;
    }, true);
    document.addEventListener('keydown', handleGlobalKeydown);
    document.addEventListener('rp:slidechange', () => {
      closeDetail();
      hideTooltip();
      updateAgenda();
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
        updateAllTermStates();
        if (isOverview()) {
          closeAgenda();
          closeSearch();
          closeDetail(false);
          hideTooltip();
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
    updateAgenda();
    applyOverlayTheme();
  }

  window.DeckOverlay = {
    init: init,
    openSearch: openSearch,
    closeSearch: closeSearch,
    openDetail: openDetail,
    closeDetail: closeDetail,
    buildIndex: buildIndex
  };
})();
