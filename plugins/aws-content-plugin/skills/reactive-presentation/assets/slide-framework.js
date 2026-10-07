/**
 * Reactive Presentation - Slide Navigation Framework
 * Keyboard (←→, Space, F, Esc) + button navigation, progress bar, slide transitions
 */
class SlideFramework {
  constructor(options = {}) {
    this.currentSlide = 0;
    this.slides = [];
    this.totalSlides = 0;
    this.transitioning = false;
    this.onSlideChange = options.onSlideChange || null;
    this.footer = options.footer || null;
    this.logoSrc = options.logoSrc || null;
    // Logo shown on dark slides (white/light logo). Falls back to logoSrc when unset.
    this.logoDarkSrc = options.logoDarkSrc || null;
    this.presenterNotes = options.presenterNotes || {};
    this.presenterView = null;
    this.slideActions = {};  // { slideIndex: { up: fn, down: fn } }
    this.pagination = options.pagination || false;
    // Fragment system
    this.fragmentState = {};  // { slideIndex: { fragments: [], currentIndex: -1 } }
    // Overview mode
    this.overviewMode = false;
    // Sidebar
    this.sidebarEnabled = options.sidebar !== false;
    this.sidebarVisible = false;
    this.sidebarWasVisible = false; // track state across fullscreen
    this.sidebar = null;
    // Custom key mappings
    this.keyMappings = {};
    this.init();
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      this.slides = Array.from(document.querySelectorAll('.slide'));
      this.totalSlides = this.slides.length;
      if (this.totalSlides === 0) return;

      // Load custom key mappings from window.__remarpKeys
      if (window.__remarpKeys && typeof window.__remarpKeys === 'object') {
        this.keyMappings = window.__remarpKeys;
      }

      // Harvest <template class="notes"> speaker notes from slide DOM.
      // Must run BEFORE createSidebar() clones slide innerHTML (a cloned
      // <template> is inert but would double-count if harvested later).
      // An explicit presenterNotes option always wins over the DOM.
      this.slides.forEach((slide, idx) => {
        const key = idx + 1;
        if (this.presenterNotes[key] !== undefined) return;
        const tpl = slide.querySelector('template.notes');
        if (!tpl) return;
        const text = tpl.content.textContent.trim();
        if (!text) return;
        const timing = tpl.dataset.timing || null;
        this.presenterNotes[key] = timing ? { text: text, timing: timing } : text;
      });

      // Read theme config
      if (window.__remarpTheme) {
        if (!this.footer && window.__remarpTheme.footer) this.footer = window.__remarpTheme.footer;
        if (window.__remarpTheme.pagination !== undefined) this.pagination = window.__remarpTheme.pagination;
      }

      this.createProgressBar();
      if (!this.pagination) this.createSlideCounter();
      this.createNavHint();
      if (this.pagination) this.createSlideNumber();
      this.createRefContainer();
      if (this.sidebarEnabled) {
        this.createSidebar();
        this.bindSidebarFullscreen();
        if (!document.fullscreenElement) {
          this.showSidebar();
        }
      }
      this.bindKeys();
      this.bindTouch();
      this.handleHash();
      this.bindDeckScale();
      if (this.footer) this.createFooter();
      if (this.logoSrc) this.createLogo();
      this.initFragments(this.currentSlide);
      this.showSlide(this.currentSlide, false);
      if (window.ReactiveFit) {
        window.ReactiveFit.fitAll();
        if (document.fonts && document.fonts.ready) {
          document.fonts.ready.then(() => window.ReactiveFit.fitAll({ force: true }));
        }
      }
    });
  }

  // Fragment system methods
  initFragments(slideIndex) {
    const slide = this.slides[slideIndex];
    if (!slide) return;

    const fragments = Array.from(slide.querySelectorAll('.fragment'));
    // Sort by data-fragment-index if present, otherwise use DOM order
    fragments.sort((a, b) => {
      const aIdx = parseInt(a.dataset.fragmentIndex, 10) || 0;
      const bIdx = parseInt(b.dataset.fragmentIndex, 10) || 0;
      return aIdx - bIdx;
    });

    this.fragmentState[slideIndex] = {
      fragments: fragments,
      currentIndex: -1
    };
  }

  revealNextFragment() {
    const state = this.fragmentState[this.currentSlide];
    if (!state || state.fragments.length === 0) return false;

    if (state.currentIndex < state.fragments.length - 1) {
      state.currentIndex++;
      const fragment = state.fragments[state.currentIndex];
      const targetIndex = fragment.dataset.fragmentIndex;
      fragment.classList.add('visible');
      // Reveal all fragments sharing the same index
      while (state.currentIndex + 1 < state.fragments.length) {
        const next = state.fragments[state.currentIndex + 1];
        if (next.dataset.fragmentIndex === targetIndex) {
          state.currentIndex++;
          next.classList.add('visible');
        } else { break; }
      }
      return true; // Fragment revealed, don't advance slide
    }
    return false; // All fragments revealed, can advance slide
  }

  revealPrevFragment() {
    const state = this.fragmentState[this.currentSlide];
    if (!state || state.fragments.length === 0) return false;

    if (state.currentIndex >= 0) {
      const fragment = state.fragments[state.currentIndex];
      const targetIndex = fragment.dataset.fragmentIndex;
      fragment.classList.remove('visible');
      // Hide all fragments sharing the same index (backwards)
      while (state.currentIndex - 1 >= 0) {
        const prev = state.fragments[state.currentIndex - 1];
        if (prev.dataset.fragmentIndex === targetIndex) {
          state.currentIndex--;
          prev.classList.remove('visible');
        } else { break; }
      }
      state.currentIndex--;
      return true; // Fragment hidden, don't go back slide
    }
    return false; // No fragments to hide, can go back slide
  }

  resetFragments(slideIndex) {
    const state = this.fragmentState[slideIndex];
    if (!state) return;

    state.fragments.forEach(f => f.classList.remove('visible'));
    state.currentIndex = -1;
  }

  hasUnrevealedFragments() {
    const state = this.fragmentState[this.currentSlide];
    if (!state || state.fragments.length === 0) return false;
    return state.currentIndex < state.fragments.length - 1;
  }

  // Overview mode methods
  toggleOverview() {
    this.overviewMode = !this.overviewMode;
    const deck = this.getDeck();
    if (!deck) return;

    if (this.overviewMode) {
      deck.classList.add('overview-mode');
      this.slides.forEach((slide, idx) => {
        slide.classList.add('overview-visible');
        slide.classList.toggle('current', idx === this.currentSlide);
        slide.onclick = () => {
          this.goTo(idx);
          this.toggleOverview();
        };
      });
    } else {
      deck.classList.remove('overview-mode');
      this.slides.forEach(slide => {
        slide.classList.remove('overview-visible', 'current');
        slide.onclick = null;
      });
      this.showSlide(this.currentSlide, false);
      this.updateDeckScale(); // overview is height:auto — rescale to the restored canvas
    }
  }

  // Sidebar methods
  createSidebar() {
    const sidebar = document.createElement('div');
    sidebar.className = 'slide-sidebar';

    this.slides.forEach((slide, idx) => {
      const thumb = document.createElement('div');
      thumb.className = 'sidebar-thumb';
      thumb.dataset.index = idx;

      const content = document.createElement('div');
      content.className = 'sidebar-thumb-content';
      content.innerHTML = slide.innerHTML;

      // Calculate scale after layout: thumbWidth / 1920
      // Use a fixed approximation; actual width is ~196px (220 - 2*10 padding - 2*2 border)
      const thumbWidth = 196;
      const scale = thumbWidth / 1920;
      content.style.transform = `scale(${scale})`;

      const number = document.createElement('span');
      number.className = 'sidebar-thumb-number';
      number.textContent = idx + 1;

      thumb.appendChild(content);
      thumb.appendChild(number);
      thumb.addEventListener('click', () => this.goTo(idx));
      sidebar.appendChild(thumb);
    });

    document.body.prepend(sidebar);
    this.sidebar = sidebar;
  }

  toggleSidebar() {
    if (this.sidebarVisible) {
      this.hideSidebar();
    } else {
      this.showSidebar();
    }
  }

  showSidebar() {
    if (!this.sidebar) return;
    document.body.classList.add('sidebar-visible');
    this.sidebarVisible = true;
    this.updateSidebarHighlight(this.currentSlide);
    this.updateDeckScale();
  }

  hideSidebar() {
    if (!this.sidebar) return;
    document.body.classList.remove('sidebar-visible');
    this.sidebarVisible = false;
    this.updateDeckScale();
  }

  updateSidebarHighlight(index) {
    if (!this.sidebar) return;
    const thumbs = this.sidebar.querySelectorAll('.sidebar-thumb');
    thumbs.forEach(t => t.classList.remove('active'));
    if (thumbs[index]) {
      thumbs[index].classList.add('active');
      thumbs[index].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  bindSidebarFullscreen() {
    document.addEventListener('fullscreenchange', () => {
      if (document.fullscreenElement) {
        // Entering fullscreen — remember state and hide
        this.sidebarWasVisible = this.sidebarVisible;
        this.hideSidebar();
      } else {
        // Exiting fullscreen — restore previous state
        if (this.sidebarWasVisible) {
          this.showSidebar();
        }
      }
    });
  }

  // Get action for a key (supports custom mappings)
  getKeyAction(key) {
    // Check custom mappings first
    if (this.keyMappings[key]) {
      return this.keyMappings[key];
    }
    // Default mappings
    const defaults = {
      'ArrowRight': 'next',
      ' ': 'next',
      'PageDown': 'next',
      'ArrowLeft': 'prev',
      'PageUp': 'prev',
      'ArrowDown': 'down',
      'ArrowUp': 'up',
      'Home': 'first',
      'End': 'last',
      'p': 'presenter',
      'P': 'presenter',
      'f': 'fullscreen',
      'F': 'fullscreen',
      'o': 'overview',
      'O': 'overview',
      's': 'sidebar',
      'S': 'sidebar',
      'Escape': 'escape'
    };
    return defaults[key] || null;
  }

  registerSlideAction(slideIndex, handlers) {
    this.slideActions[slideIndex] = handlers;  // { up: fn, down: fn }
  }

  getDeck() {
    return document.querySelector('.slide-deck');
  }

  // Fixed design-canvas scaling: the deck is a fixed 1920x1080 (ratio-derived)
  // box; scale it as one unit so type, px coordinates and canvases all shrink
  // proportionally. Pairs with the .slide-deck transform in theme.css.
  updateDeckScale() {
    const deck = this.getDeck();
    if (!deck) return;
    const sidebarPad = (this.sidebarVisible && !document.fullscreenElement) ? 220 : 0;
    const availW = window.innerWidth - sidebarPad;
    const availH = window.innerHeight;
    // offsetWidth/Height are layout size, unaffected by the transform itself
    const w = deck.offsetWidth || 1920;
    const h = deck.offsetHeight || 1080;
    deck.style.setProperty('--deck-scale', Math.min(availW / w, availH / h));
  }

  bindDeckScale() {
    this.updateDeckScale();
    window.addEventListener('resize', () => this.updateDeckScale());
    document.addEventListener('fullscreenchange', () => this.updateDeckScale());
  }

  // Framework chrome (logo, footer, slide number, refs) yields only to a full-bleed visual:
  // the slide (or an element in it) carries data-hide-chrome or .full-bleed, or one <img>
  // covers at least FULL_BLEED_AREA of the slide. Inline images — service icons, a diagram
  // or screenshot in a column — keep the chrome. data-keep-chrome on the slide always keeps
  // it. Both rects come from getBoundingClientRect, so the deck transform and the
  // ReactiveFit zoom cancel out of the ratio.
  slideHidesChrome(slide) {
    const FULL_BLEED_AREA = 0.6;
    if (slide.hasAttribute('data-keep-chrome')) return false;
    if (slide.matches('.full-bleed, [data-hide-chrome]') ||
        slide.querySelector('.full-bleed, [data-hide-chrome]')) return true;
    const sr = slide.getBoundingClientRect();
    const slideArea = sr.width * sr.height;
    if (!(slideArea > 0)) return false;
    return Array.from(slide.querySelectorAll('img')).some(img => {
      const r = img.getBoundingClientRect();
      const w = Math.min(r.right, sr.right) - Math.max(r.left, sr.left);
      const h = Math.min(r.bottom, sr.bottom) - Math.max(r.top, sr.top);
      return w > 0 && h > 0 && (w * h) / slideArea >= FULL_BLEED_AREA;
    });
  }

  updateFooterVisibility(slide) {
    const deck = this.getDeck() || document.body;
    const logo = deck.querySelector('.slide-logo');
    const footer = deck.querySelector('.slide-footer');
    const hide = this.slideHidesChrome(slide);
    // An image that has not loaded yet may have no box: re-check once it loads.
    slide.querySelectorAll('img').forEach(img => {
      if (img.complete || img.__chromeRecheck) return;
      img.__chromeRecheck = true;
      img.addEventListener('load', () => {
        if (this.slides && this.slides[this.currentSlide] === slide) this.updateFooterVisibility(slide);
      }, { once: true });
    });
    if (logo) {
      logo.style.display = hide ? 'none' : '';
      // Per-slide adaptive logo: dark slides show the light/white logo, light slides
      // show the default (dark) logo. A slide is "dark" when it (or the deck) carries
      // the theme-dark class. Only swaps when a distinct dark logo was supplied.
      if (this.logoDarkSrc) {
        const deckDark = (this.getDeck() || document.body).classList.contains('theme-dark');
        const slideDark = slide.classList.contains('theme-dark') ||
          (deckDark && !slide.classList.contains('theme-light'));
        const want = slideDark ? this.logoDarkSrc : this.logoSrc;
        if (want && logo.getAttribute('src') !== want) logo.src = want;
      }
    }
    if (footer) footer.style.display = hide ? 'none' : '';
    const slideNum = deck.querySelector('.slide-number');
    if (slideNum) slideNum.style.display = hide ? 'none' : '';
    const slideRef = deck.querySelector('.slide-ref');
    if (slideRef) slideRef.style.display = hide ? 'none' : '';
  }

  createFooter() {
    const footer = document.createElement('div');
    footer.className = 'slide-footer';
    footer.textContent = this.footer;
    (this.getDeck() || document.body).appendChild(footer);
  }

  createLogo() {
    const logo = document.createElement('img');
    logo.className = 'slide-logo';
    logo.src = this.logoSrc;
    logo.alt = 'Logo';
    (this.getDeck() || document.body).appendChild(logo);
  }

  openPresenterView() {
    if (!this.presenterView) {
      this.presenterView = new PresenterView(this);
    }
    this.presenterView.open();
  }

  createProgressBar() {
    const bar = document.createElement('div');
    bar.className = 'progress-bar';
    (this.getDeck() || document.body).appendChild(bar);
    this.progressBar = bar;
  }

  createSlideCounter() {
    const counter = document.createElement('div');
    counter.className = 'slide-counter';
    (this.getDeck() || document.body).appendChild(counter);
    this.counter = counter;
  }

  createNavHint() {
    const hint = document.createElement('div');
    hint.className = 'nav-hint';
    hint.textContent = '← → Space  |  F: Fullscreen  |  P: Presenter  |  O: Overview';
    // Footer occupies the same bottom-left corner — lift the hint above it
    if (this.footer) hint.style.bottom = '2.2rem';
    (this.getDeck() || document.body).appendChild(hint);
    this.navHint = hint;
    // Fade out after 5s
    setTimeout(() => { hint.style.opacity = '0'; }, 5000);
  }

  createSlideNumber() {
    const el = document.createElement('div');
    el.className = 'slide-number';
    (this.getDeck() || document.body).appendChild(el);
    this.slideNumber = el;
  }

  createRefContainer() {
    const el = document.createElement('div');
    el.className = 'slide-ref';
    (this.getDeck() || document.body).appendChild(el);
    this.refContainer = el;
  }

  bindKeys() {
    document.addEventListener('keydown', (e) => {
      // Don't navigate if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      const action = this.getKeyAction(e.key);
      if (!action) return;

      switch (action) {
        case 'next':
          e.preventDefault();
          if (this.overviewMode) return;
          if (!this.revealNextFragment()) {
            this.next();
          }
          break;
        case 'prev':
          e.preventDefault();
          if (this.overviewMode) return;
          if (!this.revealPrevFragment()) {
            this.prev();
          }
          break;
        case 'down':
          e.preventDefault();
          if (this.slideActions[this.currentSlide] && this.slideActions[this.currentSlide].down) {
            const result = this.slideActions[this.currentSlide].down();
            if (result === false) this.next();
          } else if (!this.cycleInteractive(1)) {
            if (!this.revealNextFragment()) {
              this.next();
            }
          }
          break;
        case 'up':
          e.preventDefault();
          if (this.slideActions[this.currentSlide] && this.slideActions[this.currentSlide].up) {
            const result = this.slideActions[this.currentSlide].up();
            if (result === false) this.prev();
          } else if (!this.cycleInteractive(-1)) {
            if (!this.revealPrevFragment()) {
              this.prev();
            }
          }
          break;
        case 'first':
          e.preventDefault();
          this.goTo(0);
          break;
        case 'last':
          e.preventDefault();
          this.goTo(this.totalSlides - 1);
          break;
        case 'presenter':
          e.preventDefault();
          this.openPresenterView();
          break;
        case 'fullscreen':
          e.preventDefault();
          this.toggleFullscreen();
          break;
        case 'overview':
          e.preventDefault();
          this.toggleOverview();
          break;
        case 'sidebar':
          e.preventDefault();
          if (!document.fullscreenElement) this.toggleSidebar();
          break;
        case 'escape':
          if (this.overviewMode) {
            this.toggleOverview();
          } else if (document.fullscreenElement) {
            document.exitFullscreen();
          }
          break;
      }
    });
  }

  bindTouch() {
    let startX = 0;
    const deck = document.querySelector('.slide-deck');
    if (!deck) return;

    deck.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
    }, { passive: true });

    deck.addEventListener('touchend', (e) => {
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) {
        if (dx < 0) {
          if (!this.revealNextFragment()) this.next();
        } else {
          if (!this.revealPrevFragment()) this.prev();
        }
      }
    }, { passive: true });
  }

  handleHash() {
    const hash = window.location.hash;
    if (hash) {
      const num = parseInt(hash.replace('#', ''), 10);
      if (!isNaN(num) && num >= 1 && num <= this.totalSlides) {
        this.currentSlide = num - 1;
      }
    }
  }

  showSlide(index, animate = true) {
    if (index < 0 || index >= this.totalSlides) return;
    if (this.transitioning) return;
    if (this.overviewMode) return; // Don't animate in overview mode

    const prevIndex = this.currentSlide;
    const prev = this.slides[prevIndex];
    const next = this.slides[index];

    // Reset fragments on previous slide
    if (prevIndex !== index) {
      this.resetFragments(prevIndex);
    }

    // Initialize fragments for next slide
    if (!this.fragmentState[index]) {
      this.initFragments(index);
    }

    // Get transition type from slide's data-transition attribute
    const transition = next.dataset.transition || 'fade';

    if (animate && prev !== next) {
      this.transitioning = true;
      prev.classList.remove('active');
      prev.classList.add('leaving');

      // Add transition-specific classes
      prev.classList.add(`transition-${transition}-out`);
      next.classList.add('entering');
      next.classList.add(`transition-${transition}-in`);

      setTimeout(() => {
        prev.classList.remove('leaving', `transition-${transition}-out`);
        next.classList.remove('entering', `transition-${transition}-in`);
        next.classList.add('active');
        this.transitioning = false;
      }, 350);
    } else {
      this.slides.forEach(s => s.classList.remove('active'));
      next.classList.add('active');
    }

    if (window.ReactiveFit) window.ReactiveFit.fitSlide(next);

    this.currentSlide = index;
    this.updateProgress();
    if (this.sidebar) this.updateSidebarHighlight(index);
    this.updateFooterVisibility(next);
    this.updateRefs(next);
    window.location.hash = index + 1;

    if (this.onSlideChange) {
      this.onSlideChange(index, next);
    }

    // Sync with presenter view
    if (this.presenterView) {
      this.presenterView.broadcastSlideChange(index);
      this.presenterView.updatePresenterView();
    }
  }

  next() { this.showSlide(this.currentSlide + 1); }
  prev() { this.showSlide(this.currentSlide - 1); }
  goTo(index) { this.showSlide(index); }

  updateProgress() {
    const pct = ((this.currentSlide + 1) / this.totalSlides) * 100;
    if (this.progressBar) this.progressBar.style.width = pct + '%';
    if (this.counter) this.counter.textContent = `${this.currentSlide + 1} / ${this.totalSlides}`;
    if (this.slideNumber) {
      this.slideNumber.textContent = (this.currentSlide + 1) + ' / ' + this.totalSlides;
    }
  }

  updateRefs(slide) {
    if (!this.refContainer) return;
    const refsData = slide.dataset.refs;
    if (!refsData) { this.refContainer.innerHTML = ''; return; }
    try {
      const refs = JSON.parse(refsData);
      this.refContainer.innerHTML = refs.map(r =>
        '<a href="' + r.url + '" target="_blank" rel="noopener">' + r.label + '</a>'
      ).join(' &middot; ');
    } catch(e) { this.refContainer.innerHTML = ''; }
  }

  toggleFullscreen() {
    if (!document.fullscreenElement) {
      // Fullscreen the document ROOT, not .slide-deck: the UA's !important
      // :fullscreen rules (width/height:100%, transform:none) cannot be
      // overridden by author CSS and would defeat the fixed 1920x1080 canvas
      // + --deck-scale model. With the root fullscreen the deck stays a
      // centered child of body and updateDeckScale() (bound to
      // fullscreenchange) fits it to the screen.
      const root = document.documentElement;
      if (root && root.requestFullscreen) root.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen();
    }
  }

  cycleInteractive(direction) {
    const slide = this.slides[this.currentSlide];
    if (!slide) return false;

    // Try canvas/timeline step navigation (registered via __canvasStep)
    if (slide.__canvasStep) {
      const dir = direction > 0 ? 'next' : 'prev';
      const result = slide.__canvasStep(dir);
      if (result !== false) return true;
      return false;
    }

    // Try tabs — detect .tab-bar container first, then fall back to any .tab-btn group
    const tabBar = slide.querySelector('.tab-bar');
    const tabBtns = tabBar
      ? Array.from(tabBar.querySelectorAll('.tab-btn'))
      : Array.from(slide.querySelectorAll('.tab-btn'));
    if (tabBtns.length > 1) {
      // Detect active tab: .active class OR visually highlighted (inline background)
      let activeIdx = tabBtns.findIndex(t => t.classList.contains('active'));
      if (activeIdx < 0) {
        // Self-contained tabs use inline style instead of .active class
        activeIdx = tabBtns.findIndex(t => {
          const bg = (t.style.background || t.style.backgroundColor || '').toLowerCase();
          return bg.includes('#00d4ff') || bg.includes('var(--accent');
        });
      }
      if (activeIdx < 0) activeIdx = 0;
      const nextIdx = Math.max(0, Math.min(activeIdx + direction, tabBtns.length - 1));
      if (nextIdx !== activeIdx) {
        tabBtns[nextIdx].click();
        return true;
      }
      return false;
    }

    // Try compare toggles
    const toggle = slide.querySelector('.compare-toggle');
    if (toggle) {
      const btns = Array.from(toggle.querySelectorAll('.compare-btn'));
      const activeIdx = btns.findIndex(b => b.classList.contains('active'));
      const nextIdx = Math.max(0, Math.min(activeIdx + direction, btns.length - 1));
      if (nextIdx !== activeIdx) {
        btns[nextIdx].click();
        return true;
      }
      return false;
    }

    return false;
  }
}

// ReactiveFit — PPT-style autofit of .slide-body content via CSS `zoom`.
// Measured Chromium facts (standardized `zoom`) this code relies on:
//  - offsetHeight/scrollWidth/clientWidth of the zoomed element are reported in its
//    OWN unzoomed coordinates. The visual height inside the parent is therefore
//    `box.offsetHeight * z`, and horizontal overflow is `box.scrollWidth > box.clientWidth`
//    (clientWidth shrinks to containerWidth / z while scrollWidth stays in content units).
//  - getBoundingClientRect() would include zoom AND the outer deck transform, so it is
//    not used for the fit test.
//  - rem/px lengths scale with zoom; percentage widths do not.
(function () {
  const MIN = 0.8;
  const MAX = 1.35;
  const TARGET = 0.94;
  const STYLE_ID = 'reactive-fit-style';
  const SKIP_SELECTOR = 'canvas, iframe, .archify, .archify-diagram';

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    // Forcing fragments visible for measurement must not leave transforms mid-transition.
    style.textContent = '.fit-measuring *, .fit-measuring *::before, .fit-measuring *::after { transition: none !important; }';
    document.head.appendChild(style);
  }

  function resolveMode(slideEl, deck) {
    let mode = slideEl.dataset.fit || (deck && deck.dataset.fit) || 'auto';
    mode = String(mode).trim().toLowerCase();
    return (mode === 'shrink' || mode === 'off') ? mode : 'auto';
  }

  function fitSlide(slideEl, opts) {
    opts = opts || {};
    // 1. Only real slides, never while the deck is in overview mode.
    if (!slideEl || !slideEl.classList || !slideEl.classList.contains('slide')) return null;
    const deck = slideEl.closest('.slide-deck');
    if (deck && deck.classList.contains('overview-mode')) return null;

    // 2. Cover/title/thank-you slides have no body and are left alone.
    const body = slideEl.querySelector('.slide-body');
    if (!body) return null;

    // 3. Mode: slide -> deck -> auto.
    const mode = resolveMode(slideEl, deck);

    // 4. Off, or pixel-exact content (canvas/iframe/archify): never zoom, never wrap.
    if (mode === 'off' || slideEl.querySelector(SKIP_SELECTOR)) {
      const existing = body.querySelector(':scope > .fit-box');
      if (existing) existing.style.zoom = '';
      delete slideEl.dataset.fitScale;
      slideEl.removeAttribute('data-fit-overflow');
      return null;
    }

    // 5. Cached result.
    const cached = slideEl.dataset.fitScale;
    if (!opts.force && cached !== undefined && cached !== '') return parseFloat(cached);

    // 6. Make a display:none slide measurable (hidden, but laid out).
    let restoreStyle = false;
    let savedDisplay = '';
    let savedVisibility = '';
    if (slideEl.getClientRects().length === 0) {
      restoreStyle = true;
      savedDisplay = slideEl.style.display;
      savedVisibility = slideEl.style.visibility;
      slideEl.style.display = 'flex';
      slideEl.style.visibility = 'hidden';
    }

    try {
      // 7. Wrap the body children once so there is a single measurable, zoomable box.
      let box = body.querySelector(':scope > .fit-box');
      if (!box) {
        box = document.createElement('div');
        box.className = 'fit-box';
        while (body.firstChild) box.appendChild(body.firstChild);
        body.appendChild(box);
      }

      // 8. Disable transitions while measuring.
      slideEl.classList.add('fit-measuring');
      ensureStyle();

      // 9. Measure the final layout: force hidden fragments visible.
      const forced = Array.from(slideEl.querySelectorAll('.fragment:not(.visible)'));
      forced.forEach(f => f.classList.add('visible'));

      let z = 1;
      let overflow = false;
      try {
        // 10. body.clientHeight is unzoomed (body itself is not zoomed), so it is the
        //     real available height; compare against the box's visual height.
        const avail = body.clientHeight * TARGET;
        const fits = (zoom) => {
          box.style.zoom = String(zoom);
          return box.offsetHeight * zoom <= avail && box.scrollWidth <= box.clientWidth + 1;
        };

        // 11. Upper bound by mode; shrinkOnly never regrows past the cached value.
        let hi = mode === 'shrink' ? 1 : MAX;
        if (opts.shrinkOnly && cached !== undefined && cached !== '') {
          const c = parseFloat(cached);
          if (!isNaN(c)) hi = Math.min(hi, c);
        }

        if (avail <= 0) {
          z = 1;
        } else if (fits(hi)) {
          z = hi;
        } else if (!fits(MIN)) {
          z = MIN;
          overflow = true;
        } else {
          let lo = MIN; // fits
          let h = hi;   // does not fit
          for (let i = 0; i < 6; i++) {
            const mid = (lo + h) / 2;
            if (fits(mid)) lo = mid; else h = mid;
          }
          z = lo;
        }
        // Floor: never round up past a value that was measured to fit.
        z = Math.floor(z * 1000) / 1000;

        // 12. Apply and restore fragment state.
        box.style.zoom = String(z);
      } finally {
        forced.forEach(f => f.classList.remove('visible'));
        void box.offsetHeight; // reflow before transitions come back
        slideEl.classList.remove('fit-measuring');
      }

      // 13. Publish the result.
      slideEl.dataset.fitScale = String(z);
      if (overflow) slideEl.setAttribute('data-fit-overflow', '');
      else slideEl.removeAttribute('data-fit-overflow');
      return z;
    } finally {
      if (restoreStyle) {
        slideEl.style.display = savedDisplay;
        slideEl.style.visibility = savedVisibility;
      }
    }
  }

  function fitAll(opts) {
    document.querySelectorAll('.slide-deck .slide').forEach(slide => {
      try { fitSlide(slide, opts); } catch (e) { /* one bad slide must not stop the rest */ }
    });
  }

  window.ReactiveFit = { MIN, MAX, TARGET, fitSlide, fitAll };
})();

// Tab component helper. Groups each bar's sibling .tab-content panels into one
// .tab-panels stack (theme.css puts them in a single grid cell), so the stack is as tall
// as the tallest panel and switching tabs never moves the bar or re-centers the slide.
// Runs on DOMContentLoaded before SlideFramework.init(), i.e. before the first fit.
function initTabs() {
  document.querySelectorAll('.tab-bar').forEach(bar => {
    const tabs = bar.querySelectorAll('.tab-btn');
    const container = bar.parentElement;
    if (container && !container.querySelector(':scope > .tab-panels')) {
      const panels = Array.from(container.children).filter(c => c.classList.contains('tab-content'));
      if (panels.length > 1) {
        const stack = document.createElement('div');
        stack.className = 'tab-panels';
        container.insertBefore(stack, panels[0]);
        panels.forEach(p => stack.appendChild(p));
      }
    }
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        container.querySelectorAll('.tab-content').forEach(c => {
          c.classList.toggle('active', c.dataset.tab === target);
        });
        const s = tab.closest('.slide');
        if (s && window.ReactiveFit) window.ReactiveFit.fitSlide(s, { force: true, shrinkOnly: true });
      });
    });
  });
}

// Checklist helper with expand/collapse for detail blocks
function initChecklists() {
  document.querySelectorAll('.checklist li').forEach(item => {
    item.addEventListener('click', (e) => {
      // Don't toggle if clicking inside the detail block
      if (e.target.closest('.checklist-detail')) return;
      item.classList.toggle('checked');
      // Expand/collapse detail block if present
      const detail = item.querySelector('.checklist-detail');
      if (detail) {
        if (item.classList.contains('checked')) {
          detail.style.display = 'block';
          detail.style.maxHeight = detail.scrollHeight + 'px';
        } else {
          detail.style.maxHeight = '0';
          setTimeout(() => { detail.style.display = 'none'; }, 300);
        }
      }
    });
  });
}

// Compare toggle helper (supports side-by-side and toggle modes)
function initCompareToggles() {
  document.querySelectorAll('.compare-toggle').forEach(toggle => {
    const btns = toggle.querySelectorAll('.compare-btn');
    const container = toggle.parentElement;
    const isSideBySide = container.dataset.compareMode === 'side-by-side';

    btns.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.compare;
        btns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        if (isSideBySide) {
          // Side-by-side: both panels stay visible, highlight selected
          container.querySelectorAll('.compare-content').forEach(c => {
            c.classList.remove('compare-highlight');
            if (c.dataset.compare === target) {
              c.classList.add('compare-highlight');
            }
          });
        } else {
          // Toggle mode: show only selected panel
          container.querySelectorAll('.compare-content').forEach(c => {
            c.classList.toggle('active', c.dataset.compare === target);
          });
        }
        const s = btn.closest('.slide');
        if (s && window.ReactiveFit) window.ReactiveFit.fitSlide(s, { force: true, shrinkOnly: true });
      });
    });
  });
}

// Auto-init on load
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initChecklists();
  initCompareToggles();
});
