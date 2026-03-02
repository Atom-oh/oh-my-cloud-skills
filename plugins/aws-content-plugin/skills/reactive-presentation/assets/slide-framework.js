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
    this.presenterNotes = options.presenterNotes || {};
    this.presenterView = null;
    this.slideActions = {};  // { slideIndex: { up: fn, down: fn } }
    this.init();
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      this.slides = Array.from(document.querySelectorAll('.slide'));
      this.totalSlides = this.slides.length;
      if (this.totalSlides === 0) return;

      this.createProgressBar();
      this.createSlideCounter();
      this.createNavHint();
      this.bindKeys();
      this.bindTouch();
      this.handleHash();
      if (this.footer) this.createFooter();
      if (this.logoSrc) this.createLogo();
      this.showSlide(this.currentSlide, false);
    });
  }

  registerSlideAction(slideIndex, handlers) {
    this.slideActions[slideIndex] = handlers;  // { up: fn, down: fn }
  }

  getDeck() {
    return document.querySelector('.slide-deck');
  }

  updateFooterVisibility(slide) {
    const deck = this.getDeck() || document.body;
    const logo = deck.querySelector('.slide-logo');
    const footer = deck.querySelector('.slide-footer');
    // Hide framework logo/footer when the current slide already contains an <img>
    const hide = slide.querySelector('img') !== null;
    if (logo) logo.style.display = hide ? 'none' : '';
    if (footer) footer.style.display = hide ? 'none' : '';
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
    hint.textContent = '← → Space  |  F: Fullscreen  |  P: Presenter';
    (this.getDeck() || document.body).appendChild(hint);
    this.navHint = hint;
    // Fade out after 5s
    setTimeout(() => { hint.style.opacity = '0'; }, 5000);
  }

  bindKeys() {
    document.addEventListener('keydown', (e) => {
      // Don't navigate if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      switch (e.key) {
        case 'ArrowRight':
        case ' ':
        case 'PageDown':
          e.preventDefault();
          this.next();
          break;
        case 'ArrowLeft':
        case 'PageUp':
          e.preventDefault();
          this.prev();
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (this.slideActions[this.currentSlide]?.down) {
            this.slideActions[this.currentSlide].down();
          } else {
            this.cycleInteractive(1);
          }
          break;
        case 'ArrowUp':
          e.preventDefault();
          if (this.slideActions[this.currentSlide]?.up) {
            this.slideActions[this.currentSlide].up();
          } else {
            this.cycleInteractive(-1);
          }
          break;
        case 'Home':
          e.preventDefault();
          this.goTo(0);
          break;
        case 'End':
          e.preventDefault();
          this.goTo(this.totalSlides - 1);
          break;
        case 'p':
        case 'P':
          e.preventDefault();
          this.openPresenterView();
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          this.toggleFullscreen();
          break;
        case 'Escape':
          if (document.fullscreenElement) {
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
        dx < 0 ? this.next() : this.prev();
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

    const prev = this.slides[this.currentSlide];
    const next = this.slides[index];

    if (animate && prev !== next) {
      this.transitioning = true;
      prev.classList.remove('active');
      prev.classList.add('leaving');
      next.classList.add('entering');

      setTimeout(() => {
        prev.classList.remove('leaving');
        next.classList.remove('entering');
        next.classList.add('active');
        this.transitioning = false;
      }, 350);
    } else {
      this.slides.forEach(s => s.classList.remove('active'));
      next.classList.add('active');
    }

    this.currentSlide = index;
    this.updateProgress();
    this.updateFooterVisibility(next);
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
  }

  toggleFullscreen() {
    const deck = document.querySelector('.slide-deck');
    if (!deck) return;
    if (!document.fullscreenElement) {
      deck.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen();
    }
  }

  cycleInteractive(direction) {
    const slide = this.slides[this.currentSlide];
    if (!slide) return;

    // Try tabs
    const tabBar = slide.querySelector('.tab-bar');
    if (tabBar) {
      const tabs = Array.from(tabBar.querySelectorAll('.tab-btn'));
      const activeIdx = tabs.findIndex(t => t.classList.contains('active'));
      const nextIdx = Math.max(0, Math.min(activeIdx + direction, tabs.length - 1));
      if (nextIdx !== activeIdx) tabs[nextIdx].click();
      return;
    }

    // Try compare toggles
    const toggle = slide.querySelector('.compare-toggle');
    if (toggle) {
      const btns = Array.from(toggle.querySelectorAll('.compare-btn'));
      const activeIdx = btns.findIndex(b => b.classList.contains('active'));
      const nextIdx = Math.max(0, Math.min(activeIdx + direction, btns.length - 1));
      if (nextIdx !== activeIdx) btns[nextIdx].click();
      return;
    }
  }
}

// Tab component helper
function initTabs() {
  document.querySelectorAll('.tab-bar').forEach(bar => {
    const tabs = bar.querySelectorAll('.tab-btn');
    const container = bar.parentElement;
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        container.querySelectorAll('.tab-content').forEach(c => {
          c.classList.toggle('active', c.dataset.tab === target);
        });
      });
    });
  });
}

// Checklist helper
function initChecklists() {
  document.querySelectorAll('.checklist li').forEach(item => {
    item.addEventListener('click', () => {
      item.classList.toggle('checked');
    });
  });
}

// Compare toggle helper
function initCompareToggles() {
  document.querySelectorAll('.compare-toggle').forEach(toggle => {
    const btns = toggle.querySelectorAll('.compare-btn');
    const container = toggle.parentElement;
    btns.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.compare;
        btns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        container.querySelectorAll('.compare-content').forEach(c => {
          c.classList.toggle('active', c.dataset.compare === target);
        });
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
