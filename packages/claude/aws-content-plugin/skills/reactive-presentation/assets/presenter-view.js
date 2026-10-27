/**
 * Presenter View - Dual window slide presentation with notes, timer, and sync
 * Press 'P' to open presenter view (handled by SlideFramework)
 * Draggable splitters between slides/notes and current/next slide
 * Copies main document stylesheets for faithful slide preview rendering
 */
class PresenterView {
  constructor(framework) {
    this.framework = framework;
    this.presenterWindow = null;
    this.channel = new BroadcastChannel('slide-sync');
    this.startTime = null;
    this.timerInterval = null;
    this.windowId = 'main';
    this.fragmentObserver = null;
    this.fragmentRenderTimer = null;
    this._pen = null;
    this.setupSync();
  }

  setupSync() {
    this.channel.onmessage = (e) => {
      if (e.data.type === 'goto' && e.data.source !== this.windowId) {
        this.framework.showSlide(e.data.index, true);
        if (this.presenterWindow && !this.presenterWindow.closed) {
          this.updatePresenterView();
        }
      }
    };
  }

  broadcastSlideChange(index) {
    this.channel.postMessage({
      type: 'goto',
      index: index,
      source: this.windowId
    });
  }

  open() {
    if (this.presenterWindow && !this.presenterWindow.closed) {
      this.presenterWindow.focus();
      return;
    }
    // A window closed without pagehide still holds a surface: drop it first.
    this._destroyPen();

    const html = this.createPresenterHTML();
    this.presenterWindow = window.open('', 'presenter', 'width=1200,height=800');
    this.presenterWindow.document.write(html);
    this.presenterWindow.document.close();

    const presenterRoot = this.presenterWindow.document.documentElement;
    presenterRoot.lang = document.documentElement.lang;
    presenterRoot.className = document.documentElement.className;
    presenterRoot.style.setProperty(
      'font-size',
      getComputedStyle(document.documentElement).fontSize,
      'important'
    );

    if (!this.startTime) {
      this.startTime = Date.now();
    }

    // Expose scale update callback for presenter window's splitter script
    window.__pvScaleUpdate = () => this._updateAllScales();

    this.setupPresenterControls();
    this._attachPen();
    this.startTimer();

    // Defer first render to allow presenter window layout to calculate
    setTimeout(() => this.updatePresenterView(), 300);
  }

  _collectStyleSheets() {
    let sheets = '';
    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
      sheets += `<link rel="stylesheet" href="${link.href}">\n`;
    });
    document.querySelectorAll('style').forEach(style => {
      sheets += `<style>${style.textContent}</style>\n`;
    });
    return sheets;
  }

  // Pen canvas and badge styles. A deck that links deck-pen.css already has
  // them copied by _collectStyleSheets; otherwise link the file next to deck-pen.js.
  _penStyleSheet() {
    const pen = window.DeckPen;
    if (!pen || !pen.controller || !pen.cssHref) return '';
    if (document.querySelector('link[rel="stylesheet"][href*="deck-pen.css"]')) return '';
    const inline = Array.from(document.querySelectorAll('style'))
      .some(style => style.textContent.indexOf('.rp-pen-canvas') >= 0);
    return inline ? '' : `<link rel="stylesheet" href="${pen.cssHref}">\n`;
  }

  createPresenterHTML() {
    const styleSheets = this._collectStyleSheets() + this._penStyleSheet();
    const baseHref = window.location.href.split('#')[0];

    return `<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<base href="${baseHref}">
<title>Presenter View - ${document.title}</title>
${styleSheets}
<style>
  /* === Override theme.css globals for presenter window === */
  body {
    background: #1a1a2e !important;
    color: #e8eaf0 !important;
    height: 100vh !important;
    width: auto !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    user-select: none !important;
    align-items: stretch !important;
    justify-content: stretch !important;
    margin: 0 !important;
  }

  /* === Presenter UI === */
  .presenter-topbar,
  .presenter-notes,
  .presenter-nav {
    font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 16px;
  }
  .presenter-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 20px;
    background: #0f0f1a;
    border-bottom: 1px solid #2d3250;
    flex-shrink: 0;
  }
  .presenter-timer {
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    color: var(--accent, #ec7211);
  }
  .presenter-counter {
    font-family: 'JetBrains Mono', monospace;
    font-size: 17.6px;
    color: #9ba1b8;
  }
  .presenter-title {
    font-size: 16px;
    color: #6b7194;
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .presenter-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }

  .presenter-slides {
    display: flex;
    overflow: hidden;
    min-height: 80px;
  }
  .presenter-current {
    position: relative;
    background: #0f1117;
    overflow: hidden;
    min-width: 100px;
  }
  .presenter-next {
    position: relative;
    background: #0a0a12;
    overflow: hidden;
    min-width: 60px;
  }
  .slide-label {
    position: absolute;
    top: 6px;
    left: 10px;
    font-size: 11.2px;
    color: #6b7194;
    background: rgba(15, 17, 23, 0.9);
    padding: 2px 8px;
    border-radius: 4px;
    z-index: 10;
  }
  .slide-preview {
    width: 100%;
    height: 100%;
    overflow: hidden;
    position: relative;
  }

  /* === Slide preview scaler === */
  .slide-scaler {
    position: absolute;
    top: 0;
    left: 0;
    transform-origin: top left;
    overflow: hidden;
    background: var(--bg-primary, #0f1117);
    border-radius: 4px;
  }
  .slide-scaler .slide-deck {
    width: 100% !important;
    height: 100% !important;
    max-width: none !important;
    max-height: none !important;
    position: relative !important;
    overflow: hidden !important;
    margin: 0 !important;
  }
  .slide-scaler .slide {
    display: flex !important;
    opacity: 1 !important;
    position: absolute !important;
    inset: 0 !important;
    animation: none !important;
    transition: none !important;
  }
  /* Hide framework chrome in previews */
  .slide-scaler .progress-bar,
  .slide-scaler .slide-counter,
  .slide-scaler .slide-footer,
  .slide-scaler .slide-logo,
  .slide-scaler .nav-hint {
    display: none !important;
  }
  .slide-scaler .rp-detail {
    text-decoration: none !important;
  }
  .slide-scaler .rp-detail::after {
    visibility: hidden !important;
  }

  /* === Splitters === */
  .splitter-v {
    width: 6px;
    background: #2d3250;
    cursor: col-resize;
    flex-shrink: 0;
    position: relative;
    transition: background 150ms;
  }
  .splitter-v:hover, .splitter-v.dragging {
    background: var(--accent, #ec7211);
  }
  .splitter-v::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 1px;
    width: 4px;
    height: 32px;
    transform: translateY(-50%);
    border-left: 1px solid #6b7194;
    border-right: 1px solid #6b7194;
  }

  .splitter-h {
    height: 6px;
    background: #2d3250;
    cursor: row-resize;
    flex-shrink: 0;
    position: relative;
    transition: background 150ms;
  }
  .splitter-h:hover, .splitter-h.dragging {
    background: var(--accent, #ec7211);
  }
  .splitter-h::after {
    content: '';
    position: absolute;
    left: 50%;
    top: 1px;
    height: 4px;
    width: 32px;
    transform: translateX(-50%);
    border-top: 1px solid #6b7194;
    border-bottom: 1px solid #6b7194;
  }

  /* === Notes === */
  .presenter-notes {
    overflow-y: auto;
    padding: 14px 24px;
    background: #0f0f1a;
    min-height: 80px;
  }
  .presenter-notes h3 {
    font-size: 12.8px;
    color: #6b7194;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .presenter-notes .notes-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }
  .presenter-notes .timing-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    background: var(--accent-subtle, rgba(236, 114, 17, 0.15));
    border: 1px solid var(--accent, #ec7211);
    border-radius: 12px;
    font-size: 12px;
    color: var(--accent, #ec7211);
    font-family: 'JetBrains Mono', monospace;
  }
  .presenter-notes .notes-content {
    font-size: 20.8px;
    line-height: 1.7;
    color: #dde0e8;
    word-break: keep-all;
  }
  .presenter-notes .notes-content p { margin: 0.5em 0; }
  .presenter-notes .notes-content ul, .presenter-notes .notes-content ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
  }
  .presenter-notes .notes-content li { margin: 0.3em 0; }
  .presenter-notes .notes-content strong { color: #fff; font-weight: 600; }
  .presenter-notes .notes-content code {
    background: var(--accent-subtle, rgba(236, 114, 17, 0.15));
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9em;
  }

  /* === Cue Markers === */
  .cue-markers {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }
  .cue-marker {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12.8px;
    font-weight: 500;
  }
  .cue-marker.demo {
    background: rgba(116, 185, 255, 0.15);
    color: #74b9ff;
    border: 1px solid rgba(116, 185, 255, 0.3);
  }
  .cue-marker.pause {
    background: rgba(253, 203, 110, 0.15);
    color: #fdcb6e;
    border: 1px solid rgba(253, 203, 110, 0.3);
  }
  .cue-marker.question {
    background: rgba(0, 184, 148, 0.15);
    color: #00b894;
    border: 1px solid rgba(0, 184, 148, 0.3);
  }
  .cue-marker.transition {
    background: var(--accent-subtle, rgba(236, 114, 17, 0.15));
    color: var(--accent, #ec7211);
    border: 1px solid var(--accent, #ec7211);
  }

  /* === Nav === */
  .presenter-nav {
    display: flex;
    justify-content: center;
    gap: 12px;
    padding: 8px;
    background: #0f0f1a;
    border-top: 1px solid #2d3250;
    flex-shrink: 0;
  }
  .presenter-nav button {
    padding: 6px 20px;
    border: 1px solid #2d3250;
    border-radius: 6px;
    background: #232740;
    color: #e8eaf0;
    cursor: pointer;
    font-size: 13.6px;
    transition: all 150ms ease;
  }
  .presenter-nav button:hover {
    background: var(--accent-subtle, rgba(236, 114, 17, 0.15));
    border-color: var(--accent, #ec7211);
  }
  .end-message {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #6b7194;
    font-style: italic;
  }

  .drag-overlay {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 9999;
  }
  .drag-overlay.active { display: block; }
</style>
</head><body>

<div class="presenter-topbar">
  <span class="presenter-title" id="p-title"></span>
  <span class="presenter-timer" id="p-timer">00:00:00</span>
  <span class="presenter-counter" id="p-counter"></span>
</div>

<div class="presenter-content" id="p-content">
  <div class="presenter-slides" id="p-slides">
    <div class="presenter-current" id="p-current-wrap">
      <span class="slide-label">Current Slide</span>
      <div class="slide-preview" id="p-current"></div>
    </div>
    <div class="splitter-v" id="splitter-v"></div>
    <div class="presenter-next" id="p-next-wrap">
      <span class="slide-label">Next Slide</span>
      <div class="slide-preview" id="p-next"></div>
    </div>
  </div>
  <div class="splitter-h" id="splitter-h"></div>
  <div class="presenter-notes" id="p-notes-wrap">
    <div class="notes-header">
      <h3>Speaker Notes</h3>
      <span class="timing-badge" id="p-timing" style="display:none;">
        <span>Target:</span>
        <span id="p-timing-value">0 min</span>
      </span>
    </div>
    <div class="cue-markers" id="p-cues"></div>
    <div class="notes-content" id="p-notes">No notes for this slide.</div>
  </div>
</div>

<div class="presenter-nav">
  <button id="p-prev">&larr; Previous</button>
  <button id="p-next-btn">Next &rarr;</button>
</div>

<div class="drag-overlay" id="drag-overlay"></div>

<script>
(function() {
  var overlay = document.getElementById('drag-overlay');

  // --- Horizontal splitter (slides vs notes) ---
  var hSplitter = document.getElementById('splitter-h');
  var content = document.getElementById('p-content');
  var slidesRow = document.getElementById('p-slides');
  var notesWrap = document.getElementById('p-notes-wrap');

  var hRatio = parseFloat(localStorage.getItem('pv-h-ratio') || '0.55');
  applyHRatio(hRatio);

  function applyHRatio(r) {
    r = Math.max(0.15, Math.min(0.85, r));
    slidesRow.style.flex = '0 0 ' + (r * 100) + '%';
    notesWrap.style.flex = '1 1 0%';
  }

  var hDragging = false;
  hSplitter.addEventListener('mousedown', function(e) {
    e.preventDefault();
    hDragging = true;
    hSplitter.classList.add('dragging');
    overlay.classList.add('active');
    overlay.style.cursor = 'row-resize';
  });

  // --- Vertical splitter (current vs next) ---
  var vSplitter = document.getElementById('splitter-v');
  var currentWrap = document.getElementById('p-current-wrap');
  var nextWrap = document.getElementById('p-next-wrap');

  var vRatio = parseFloat(localStorage.getItem('pv-v-ratio') || '0.55');
  applyVRatio(vRatio);

  function applyVRatio(r) {
    r = Math.max(0.2, Math.min(0.85, r));
    currentWrap.style.flex = '0 0 ' + (r * 100) + '%';
    nextWrap.style.flex = '1 1 0%';
  }

  var vDragging = false;
  vSplitter.addEventListener('mousedown', function(e) {
    e.preventDefault();
    vDragging = true;
    vSplitter.classList.add('dragging');
    overlay.classList.add('active');
    overlay.style.cursor = 'col-resize';
  });

  // --- Shared mousemove / mouseup ---
  document.addEventListener('mousemove', function(e) {
    if (hDragging) {
      var rect = content.getBoundingClientRect();
      var y = e.clientY - rect.top;
      hRatio = y / rect.height;
      applyHRatio(hRatio);
    }
    if (vDragging) {
      var rect = slidesRow.getBoundingClientRect();
      var x = e.clientX - rect.left;
      vRatio = x / rect.width;
      applyVRatio(vRatio);
    }
  });

  document.addEventListener('mouseup', function() {
    if (hDragging) {
      hDragging = false;
      hSplitter.classList.remove('dragging');
      localStorage.setItem('pv-h-ratio', String(Math.max(0.15, Math.min(0.85, hRatio))));
    }
    if (vDragging) {
      vDragging = false;
      vSplitter.classList.remove('dragging');
      localStorage.setItem('pv-v-ratio', String(Math.max(0.2, Math.min(0.85, vRatio))));
    }
    overlay.classList.remove('active');
    overlay.style.cursor = '';
    // Notify opener to recalculate preview scales after splitter drag
    try { window.opener && window.opener.__pvScaleUpdate && window.opener.__pvScaleUpdate(); } catch(e) {}
  });
})();
</script>
</body></html>`;
  }

  setupPresenterControls() {
    const win = this.presenterWindow;
    const doc = win.document;

    doc.getElementById('p-prev').onclick = () => {
      this.framework.prev();
      this.broadcastSlideChange(this.framework.currentSlide);
      this.updatePresenterView();
    };

    doc.getElementById('p-next-btn').onclick = () => {
      this.framework.next();
      this.broadcastSlideChange(this.framework.currentSlide);
      this.updatePresenterView();
    };

    doc.addEventListener('keydown', (e) => {
      const tag = e.target && e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
          (e.target && e.target.isContentEditable)) return;

      const action = this.framework.getKeyAction(e.key);
      switch (action) {
        case 'next':
        case 'prev':
        case 'down':
        case 'up':
        case 'first':
        case 'last':
          e.preventDefault();
          // Remote steps do not pass through the deck's overlay key listeners.
          // Dismiss blocking panels without moving focus out of this window.
          if (window.DeckOverlay) {
            window.DeckOverlay.closeSearch(false);
            window.DeckOverlay.closeDetail(false);
          }
          this.framework.handleNavigationAction(action);
          // Steps may change the current slide without triggering showSlide().
          this.updatePresenterView();
          break;
      }
    });

    doc.getElementById('p-title').textContent = document.title;

    // Recalculate scales on presenter window resize
    win.addEventListener('resize', () => this._updateAllScales());
    // Closing the presenter window drops its pen surface; the ink stays in the deck.
    win.addEventListener('pagehide', () => {
      if (this.presenterWindow === win) this._destroyPen();
    });
  }

  // Pen surface over the scaled current-slide preview. The canvas, the badge and
  // the magnifier lens (inserted by attachSurface after the canvas) are siblings
  // of #p-current, which _renderSlidePreview empties on every update.
  // isPrimary binds the pen keys on this window in the capture phase, so they
  // run once, before the document-level navigation handler below.
  _attachPen() {
    const pen = window.DeckPen;
    if (!pen || !pen.controller || !pen.attachSurface) return;
    const doc = this.presenterWindow.document;
    const wrap = doc.getElementById('p-current-wrap');
    const controller = pen.controller;

    const canvas = doc.createElement('canvas');
    canvas.id = 'rp-pen-canvas';
    canvas.className = 'rp-overlay-ui rp-pen-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    wrap.appendChild(canvas);

    const badgeEl = doc.createElement('div');
    badgeEl.id = 'rp-pen-badge';
    if (document.documentElement.lang) badgeEl.lang = document.documentElement.lang;
    wrap.appendChild(badgeEl);
    const badge = pen.buildBadge(badgeEl);

    const placeBadge = () => {
      const r = this._penRect();
      badgeEl.style.left = `${r.left}px`;
      badgeEl.style.top = `${r.top}px`;
    };
    // The presenter always sees the badge; audienceBadge only hides the deck one.
    const syncBadge = () => {
      badge.update(controller.active);
      placeBadge();
    };

    const surface = pen.attachSurface({
      doc: doc,
      canvas: canvas,
      getRect: () => this._penRect(),
      isPrimary: true,
      isInert: () => !(this._penRect().width > 0)
    });
    const unsubscribe = controller.onChange(syncBadge);
    syncBadge();

    this._pen = {
      redraw: () => {
        surface.redraw();
        placeBadge();
      },
      destroy: () => {
        unsubscribe();
        surface.destroy();
        canvas.remove();
        badgeEl.remove();
      }
    };
  }

  _destroyPen() {
    if (!this._pen) return;
    const pen = this._pen;
    this._pen = null;
    pen.destroy();
  }

  // Viewport rectangle (presenter window pixels) of the scaled slide inside
  // #p-current, from the same fit as _applyScale.
  _penRect() {
    const win = this.presenterWindow;
    const container = win && !win.closed && win.document.getElementById('p-current');
    if (!container) return { left: 0, top: 0, width: 0, height: 0 };
    const r = container.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return { left: r.left, top: r.top, width: 0, height: 0 };
    const fit = this._fit(r.width, r.height);
    return {
      left: r.left + fit.offsetX,
      top: r.top + fit.offsetY,
      width: fit.width,
      height: fit.height
    };
  }

  updatePresenterView() {
    if (!this.presenterWindow || this.presenterWindow.closed) return;

    const doc = this.presenterWindow.document;
    const idx = this.framework.currentSlide;
    const slides = this.framework.slides;

    doc.getElementById('p-counter').textContent = `${idx + 1} / ${this.framework.totalSlides}`;

    // Current slide
    const currentEl = doc.getElementById('p-current');
    this._renderSlidePreview(doc, currentEl, slides[idx], false);
    this._observeCurrentSlide(slides[idx]);

    // Next slide
    const nextEl = doc.getElementById('p-next');
    if (idx + 1 < slides.length) {
      this._renderSlidePreview(doc, nextEl, slides[idx + 1], true);
    } else {
      nextEl.innerHTML = '<div class="end-message">End of presentation</div>';
    }

    // Notes, cues, and timing
    this.updateNotes(doc, idx);
  }

  updateNotes(doc, slideIndex) {
    const noteKey = slideIndex + 1;
    const notesData = (this.framework.presenterNotes || {})[noteKey];
    const notesEl = doc.getElementById('p-notes');
    const cuesEl = doc.getElementById('p-cues');
    const timingEl = doc.getElementById('p-timing');
    const timingValueEl = doc.getElementById('p-timing-value');

    // Handle notes - can be string or object { text, cues, timing }
    let notesText = 'No notes for this slide.';
    let cues = [];
    let timing = null;

    if (typeof notesData === 'string') {
      notesText = notesData;
    } else if (notesData && typeof notesData === 'object') {
      notesText = notesData.text || notesData.notes || 'No notes for this slide.';
      cues = notesData.cues || [];
      timing = notesData.timing || null;
    }

    // Also check slide element for data-cues and data-timing attributes
    const slide = this.framework.slides[slideIndex];
    if (slide) {
      const dataCues = slide.dataset.cues;
      const dataTiming = slide.dataset.timing;
      if (dataCues) {
        try {
          cues = JSON.parse(dataCues);
        } catch (e) { /* ignore parsing errors */ }
      }
      if (dataTiming) {
        timing = dataTiming;
      }
    }

    // Render rich notes as HTML
    notesEl.innerHTML = this.renderRichNotes(notesText);

    // Render cue markers
    this.renderCueMarkers(cuesEl, cues);

    // Render timing badge
    if (timing) {
      timingEl.style.display = 'inline-flex';
      timingValueEl.textContent = timing;
    } else {
      timingEl.style.display = 'none';
    }
  }

  renderRichNotes(text) {
    if (!text) return 'No notes for this slide.';

    // Convert markdown-like formatting to HTML
    let html = text
      // Escape HTML first
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Line breaks
      .replace(/\n/g, '<br>');

    // Handle bullet lists (lines starting with - or *)
    html = html.replace(/(<br>|^)([-*]\s)(.+?)(?=<br>[-*]\s|<br>[^-*]|$)/g, (match, br, bullet, content) => {
      return `${br}<li>${content}</li>`;
    });

    // Wrap consecutive <li> items in <ul>
    html = html.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

    return html;
  }

  renderCueMarkers(container, cues) {
    container.innerHTML = '';
    if (!cues || !Array.isArray(cues) || cues.length === 0) return;

    const cueIcons = {
      demo: { icon: '🎬', label: 'Demo' },
      pause: { icon: '⏸', label: 'Pause' },
      question: { icon: '❓', label: 'Question' },
      transition: { icon: '🔄', label: 'Transition' }
    };

    cues.forEach(cue => {
      const type = cue.type || cue;
      const label = cue.label || cueIcons[type]?.label || type;
      const icon = cueIcons[type]?.icon || '📌';

      const marker = document.createElement('div');
      marker.className = `cue-marker ${type}`;
      marker.innerHTML = `<span>${icon}</span><span>${label}</span>`;
      container.appendChild(marker);
    });
  }

  _canvasSize() {
    const liveDeck = this.framework.getDeck();
    const style = liveDeck ? getComputedStyle(liveDeck) : null;
    const computedRatioW = parseFloat(style?.getPropertyValue('--slide-ratio-w'));
    const computedRatioH = parseFloat(style?.getPropertyValue('--slide-ratio-h'));
    const ratioW = computedRatioW > 0 ? computedRatioW : 16;
    const ratioH = computedRatioH > 0 ? computedRatioH : 9;
    const h = 1080;
    return { w: Math.round(h * ratioW / ratioH), h: h };
  }

  _renderSlidePreview(doc, container, sourceSlide, revealAll) {
    container.innerHTML = '';

    const canvas = this._canvasSize();
    const scaler = doc.createElement('div');
    scaler.className = 'slide-scaler';
    scaler.style.width = `${canvas.w}px`;
    scaler.style.height = `${canvas.h}px`;

    const deck = doc.createElement('div');
    const liveDeck = sourceSlide.closest('.slide-deck') || this.framework.getDeck();
    if (liveDeck) {
      deck.className = Array.from(liveDeck.classList)
        .filter(name => name !== 'overview-mode')
        .join(' ');
      if (liveDeck.hasAttribute('data-fit')) {
        deck.setAttribute('data-fit', liveDeck.getAttribute('data-fit'));
      }
      if (liveDeck.hasAttribute('lang')) {
        deck.lang = liveDeck.lang;
      }
    } else {
      deck.className = 'slide-deck';
    }

    const clone = sourceSlide.cloneNode(true);
    clone.className = sourceSlide.className;
    Array.from(clone.classList).forEach(className => {
      if (className === 'leaving' ||
          className === 'entering' ||
          className.startsWith('transition-')) {
        clone.classList.remove(className);
      }
    });
    clone.classList.add('active');
    if (revealAll) {
      clone.querySelectorAll('.fragment').forEach(fragment => {
        fragment.classList.add('visible');
      });
    }

    deck.appendChild(clone);
    scaler.appendChild(deck);
    container.appendChild(scaler);

    // Calculate centered scale to fit container
    const rect = container.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      this._applyScale(scaler, rect.width, rect.height);
    }
    if (container.id === 'p-current' && this._pen) this._pen.redraw();
  }

  // Centred fit of the deck canvas into a container: scale, size and offset.
  _fit(containerW, containerH) {
    const canvas = this._canvasSize();
    const scale = Math.min(containerW / canvas.w, containerH / canvas.h);
    const width = canvas.w * scale;
    const height = canvas.h * scale;
    return {
      scale: scale,
      width: width,
      height: height,
      offsetX: (containerW - width) / 2,
      offsetY: (containerH - height) / 2
    };
  }

  _applyScale(scaler, containerW, containerH) {
    const fit = this._fit(containerW, containerH);
    scaler.style.transform = `translate(${fit.offsetX}px, ${fit.offsetY}px) scale(${fit.scale})`;
  }

  _observeCurrentSlide(slide) {
    if (this.fragmentObserver) {
      this.fragmentObserver.disconnect();
    }
    clearTimeout(this.fragmentRenderTimer);
    this.fragmentRenderTimer = null;
    if (!slide) return;

    this.fragmentObserver = new MutationObserver(() => {
      clearTimeout(this.fragmentRenderTimer);
      this.fragmentRenderTimer = setTimeout(() => {
        if (!this.presenterWindow || this.presenterWindow.closed) return;
        const currentEl = this.presenterWindow.document.getElementById('p-current');
        if (currentEl && slide === this.framework.slides[this.framework.currentSlide]) {
          this._renderSlidePreview(this.presenterWindow.document, currentEl, slide, false);
        }
      }, 50);
    });
    this.fragmentObserver.observe(slide, {
      attributes: true,
      attributeFilter: ['class'],
      subtree: true
    });
  }

  _updateAllScales() {
    if (!this.presenterWindow || this.presenterWindow.closed) return;
    const doc = this.presenterWindow.document;

    doc.querySelectorAll('.slide-preview').forEach(container => {
      const scaler = container.querySelector('.slide-scaler');
      if (!scaler) return;
      const rect = container.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        this._applyScale(scaler, rect.width, rect.height);
      }
    });
    if (this._pen) this._pen.redraw();
  }

  startTimer() {
    if (this.timerInterval) return;

    this.timerInterval = setInterval(() => {
      if (!this.presenterWindow || this.presenterWindow.closed) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
        this._destroyPen();
        return;
      }
      const elapsed = Date.now() - this.startTime;
      const el = this.presenterWindow.document.getElementById('p-timer');
      if (el) el.textContent = this.formatTime(elapsed);
    }, 1000);
  }

  formatTime(ms) {
    const s = Math.floor(ms / 1000);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }

  destroy() {
    if (this.fragmentObserver) {
      this.fragmentObserver.disconnect();
      this.fragmentObserver = null;
    }
    clearTimeout(this.fragmentRenderTimer);
    this.fragmentRenderTimer = null;
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
    this._destroyPen();
    if (this.presenterWindow && !this.presenterWindow.closed) {
      this.presenterWindow.close();
    }
    this.channel.close();
  }
}
