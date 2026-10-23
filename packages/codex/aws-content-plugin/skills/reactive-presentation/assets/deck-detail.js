/**
 * Reactive Presentation tooltips and detail panels.
 * Overlay roots stay outside slide content.
 */
(function() {
  'use strict';

  const overlay = window.DeckOverlay;
  if (!overlay) return;
  const { liveTerm, isOverview, makeOverlay, navigationKeys,
    restoreFocusWithoutTooltip } = overlay;
  let deck = null;
  let touchTerm = null;
  let tooltipTerm = null;
  let detailOpener = null;
  let ignoreMouseUntil = 0;
  let tooltipHideTimer = null;
  let dismissedPointerPosition = null;
  let pointerPosition = null;

  function isDismissedPointer(event) {
    // Mouse events discard the subpixel precision retained by pointer events.
    return dismissedPointerPosition && Math.trunc(event.clientX) === dismissedPointerPosition.x &&
      Math.trunc(event.clientY) === dismissedPointerPosition.y;
  }

  function tooltipIsBlocked() {
    return isOverview() || document.body.matches('.rp-detail-open, .rp-search-open, .rp-agenda-open');
  }

  function cancelTooltipHide() {
    clearTimeout(tooltipHideTimer);
    tooltipHideTimer = null;
  }

  function scheduleTooltipHide() {
    cancelTooltipHide();
    if (!tooltipTerm) return;
    tooltipHideTimer = setTimeout(() => {
      tooltipHideTimer = null;
      const tooltip = document.getElementById('rp-tooltip');
      if (tooltipTerm && (tooltipTerm.contains(document.activeElement) ||
          tooltipTerm.matches(':hover') || (tooltip && tooltip.matches(':hover')))) return;
      hideTooltip();
    }, 200);
  }

  function termIsAvailable(term) {
    // fade-out fragments are the reverse case: visible until revealed, hidden after.
    return Boolean(term && liveTerm(term) && !isOverview() &&
      !term.closest('.fragment:not(.visible):not(.fade-out), .fragment.fade-out.visible'));
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

  function createTooltip() {
    const tooltip = makeOverlay('div', 'rp-tooltip');
    tooltip.setAttribute('role', 'tooltip');
    tooltip.setAttribute('aria-hidden', 'true');
    tooltip.addEventListener('mouseenter', cancelTooltipHide);
    tooltip.addEventListener('mouseleave', scheduleTooltipHide);
  }

  function showTooltip(term) {
    const tooltip = document.getElementById('rp-tooltip');
    const tip = term && term.dataset.tip;
    if (!tooltip || !tip || !termIsAvailable(term) || tooltipIsBlocked()) return;
    cancelTooltipHide();
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
    const gap = 12 * overlay.uiScale();
    const left = Math.max(gap, Math.min(
      anchor.left + anchor.width / 2 - box.width / 2,
      window.innerWidth - box.width - gap
    ));
    let top = anchor.top - box.height - gap;
    const below = top < gap;
    if (below) top = anchor.bottom + gap;
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.dataset.placement = below ? 'below' : 'above';
    // Bridge only the horizontal overlap with the trigger, not nearby controls.
    const bridgeLeft = Math.max(anchor.left, left);
    tooltip.style.setProperty('--rp-tooltip-gap', gap + 'px');
    tooltip.style.setProperty('--rp-tooltip-bridge-left', (bridgeLeft - left) + 'px');
    tooltip.style.setProperty('--rp-tooltip-bridge-width',
      Math.max(0, Math.min(anchor.right, left + box.width) - bridgeLeft) + 'px');
  }

  function hideTooltip() {
    cancelTooltipHide();
    const tooltip = document.getElementById('rp-tooltip');
    if (!tooltip) return;
    if (tooltipTerm) {
      // Closing an overlay can synthesize mouseover without a pointer move.
      // Ignore that stationary pointer even if focus had shown a different term.
      dismissedPointerPosition = pointerPosition;
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
    if (wasOpen) overlay.blockAgendaUnderPointer();
    if (wasOpen && restoreFocus && termIsAvailable(opener)) {
      restoreFocusWithoutTooltip(opener);
    }
  }

  function bindDetailEvents() {
    document.addEventListener('pointermove', event => {
      pointerPosition = { x: Math.trunc(event.clientX), y: Math.trunc(event.clientY) };
      if (!isDismissedPointer(event)) dismissedPointerPosition = null;
    });
    document.addEventListener('pointerout', event => {
      if (event.relatedTarget) return;
      pointerPosition = null;
      dismissedPointerPosition = null;
    });
    deck.addEventListener('mouseover', event => {
      if (Date.now() < ignoreMouseUntil) return;
      const term = liveTerm(event.target);
      if (!term || isDismissedPointer(event) || term.contains(event.relatedTarget)) return;
      if (termIsAvailable(term)) showTooltip(term);
    });
    deck.addEventListener('mouseout', event => {
      const term = liveTerm(event.target);
      if (!term || term !== tooltipTerm || term.contains(event.relatedTarget)) return;
      scheduleTooltipHide();
    });
    deck.addEventListener('focusin', event => {
      const term = liveTerm(event.target);
      if (term && overlay.isSuppressedFocusTerm(term)) {
        hideTooltip();
        return;
      }
      if (termIsAvailable(term)) showTooltip(term);
    });
    deck.addEventListener('focusout', event => {
      const term = liveTerm(event.target);
      if (!term || term !== tooltipTerm || term.contains(event.relatedTarget)) return;
      scheduleTooltipHide();
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
      if (!termIsAvailable(term) || !term.dataset.detail) return;
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      event.stopPropagation();
      openDetail(term.closest('.slide'), term.dataset.detail, term);
    });

    document.addEventListener('pointerdown', event => {
      if (!document.body.classList.contains('rp-detail-open')) return;
      const panel = document.getElementById('rp-detail-panel');
      if (!panel.contains(event.target) && !liveTerm(event.target)) closeDetail();
    });
  }

  function handleKeydown(event) {
    const detailOpen = document.body.classList.contains('rp-detail-open');
    if (event.key === 'Escape' && (detailOpen || tooltipTerm)) {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (detailOpen) closeDetail();
      hideTooltip();
      return true;
    }
    if (!detailOpen) return false;
    const panel = document.getElementById('rp-detail-panel');
    if ((event.key === ' ' || event.key === 'Enter') && panel && panel.contains(event.target)) {
      // Let a focused panel control activate natively instead of advancing the deck.
      event.stopImmediatePropagation();
      return true;
    }
    if (navigationKeys.has(event.key)) closeDetail();
    return false;
  }

  function init(instance, slideDeck) {
    deck = slideDeck;
    document.querySelectorAll('.slide-sidebar .rp-detail').forEach(term => {
      term.setAttribute('tabindex', '-1');
    });
    createTooltip();
    createDetailPanel();
    updateAllTermStates();
    bindDetailEvents();
    new MutationObserver(() => {
      if (tooltipIsBlocked()) hideTooltip();
    }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  }

  overlay.register('detail', {
    priority: 1,
    init: init,
    keydown: handleKeydown,
    slideChange: () => {
      closeDetail();
      hideTooltip();
    },
    updateAllTermStates: updateAllTermStates,
    hideTooltip: hideTooltip,
    openDetail: openDetail,
    closeDetail: closeDetail,
    detailOpener: () => termIsAvailable(detailOpener) ? detailOpener : null
  });
})();
