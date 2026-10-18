/**
 * Reactive Presentation agenda and search.
 * Overlay roots stay outside slide content.
 */
(function() {
  'use strict';

  const overlay = window.DeckOverlay;
  if (!overlay) return;
  const { normalizeText, isOverview, isTypingTarget, makeOverlay,
    restoreFocusWithoutTooltip } = overlay;
  let framework = null;
  let searchIndex = [];
  let agendaCloseTimer = null;
  let selectedResult = 0;
  let previousFocus = null;
  let agendaHotzoneBlocked = false;
  let pointerX = null;
  let pointerY = null;

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
    // Inline-split words (e.g. <wbr>, <strong>) stay joined; only a block boundary
    // between two text nodes becomes a space.
    let previousBlock = null;
    while (walker.nextNode()) {
      const node = walker.currentNode;
      const block = nearestBlock(node.parentElement, slide);
      if (previousBlock && block !== previousBlock) values.push(' ');
      values.push(node.nodeValue);
      previousBlock = block;
    }
    return normalizeText(values.join(''));
  }

  function nearestBlock(element, stop) {
    let current = element;
    while (current && current !== stop &&
        getComputedStyle(current).display.startsWith('inline')) {
      current = current.parentElement;
    }
    return current || stop;
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
    let matchAt = -1;
    if (lower.length !== source.length) {
      for (let i = 0; i + query.length <= source.length; i += 1) {
        if (source.substr(i, query.length).toLocaleLowerCase() === needle) {
          matchAt = i;
          break;
        }
      }
    } else {
      matchAt = lower.indexOf(needle);
    }
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
      overlay.detailOpener() ? overlay.detailOpener() : document.activeElement;
    closeAgenda();
    overlay.closeDetail(false);
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

  function handleKeydown(event) {
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
      return true;
    }

    if (isTypingTarget(event.target) || isOverview()) return false;
    const searchShortcut = (event.metaKey || event.ctrlKey) &&
      event.key.toLocaleLowerCase() === 'k';
    if (searchShortcut || event.key === '/') {
      event.preventDefault();
      openSearch();
      return true;
    }
    return false;
  }

  function init(instance) {
    framework = instance;
    buildIndex();
    createAgenda();
    createSearch();
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
    updateAgenda();
  }

  overlay.register('nav', {
    priority: 0,
    init: init,
    keydown: handleKeydown,
    slideChange: updateAgenda,
    openSearch: openSearch,
    closeSearch: closeSearch,
    closeAgenda: closeAgenda,
    buildIndex: buildIndex,
    blockAgendaUnderPointer: blockAgendaUnderPointer
  });
})();
