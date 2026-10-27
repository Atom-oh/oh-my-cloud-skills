/* deck-pen.js - pen mode ink model, canvas renderer, cursor helper and the
 * deck-window controller (overlay module 'pen'). No DOM access at load time.
 * Coordinates are 0..1 of the slide box. */
(function () {
  'use strict';

  var MODES = ['laser', 'pen', 'highlighter', 'eraser', 'magnifier'];
  var ZOOMS = [2, 3, 4];
  var SIZES = { 1: 4, 2: 8, 3: 16 };
  var PALETTE = ['#e53935', '#fdd835', '#43a047', '#1e88e5', '#ffffff', '#000000'];
  var HIGHLIGHTER_ALPHA = 0.35;
  var HIGHLIGHTER_WIDTH_FACTOR = 3;
  var DEFAULT_COLORS = { laser: 0, pen: 0, highlighter: 1 };
  var BASE_WIDTH = 1920;

  function createModel(opts) {
    opts = opts || {};
    var fadeMs = opts.fadeMs == null ? 3000 : opts.fadeMs;
    var now = opts.now || function () { return Date.now(); };
    var bySlide = {};
    var current = null;
    // One chosen colour per drawing mode; the eraser and magnifier have none and
    // show the last drawing mode's.
    var colors = { laser: DEFAULT_COLORS.laser, pen: DEFAULT_COLORS.pen, highlighter: DEFAULT_COLORS.highlighter };
    var lastDrawMode = 'laser';
    var nextId = 1;

    // Eraser and magnifier draw nothing and have no colour of their own.
    function drawsInk(name) {
      return name !== 'eraser' && name !== 'magnifier';
    }

    function list(slide) {
      return bySlide[slide] || (bySlide[slide] = []);
    }

    function alive(stroke, t) {
      for (var i = 0; i < stroke.points.length; i++) {
        if (1 - (t - stroke.points[i].t) / fadeMs > 0) return true;
      }
      return false;
    }

    // Remove expired laser strokes so the model does not grow without bound.
    function prune(slide) {
      var t = now();
      var kept = list(slide).filter(function (s) {
        return s === current || s.mode !== 'laser' || alive(s, t);
      });
      bySlide[slide] = kept;
      return kept;
    }

    var model = {
      mode: 'laser',
      size: 2,
      // Magnifier zoom factor, a setting separate from the pen size.
      zoom: 2,
      // Read-only view of the colour the current mode uses.
      get colorIndex() { return this.effectiveColor(); },

      setMode: function (name) {
        if (MODES.indexOf(name) < 0) return;
        this.mode = name;
        if (drawsInk(name)) lastDrawMode = name;
      },
      setZoom: function (n) {
        if (ZOOMS.indexOf(n) >= 0) this.zoom = n;
      },
      setSize: function (n) {
        if (Object.prototype.hasOwnProperty.call(SIZES, n)) this.size = Number(n);
      },
      setColor: function (i) {
        if (!drawsInk(this.mode)) return;
        if (typeof i === 'number' && i % 1 === 0 && i >= 0 && i < PALETTE.length) {
          colors[this.mode] = i;
        }
      },

      // Palette index the current mode draws with (each drawing mode keeps its own).
      effectiveColor: function () {
        return colors[drawsInk(this.mode) ? this.mode : lastDrawMode];
      },

      // Returns the new stroke id, or null in eraser or magnifier mode (no stroke
      // is created).
      begin: function (slide, x, y) {
        if (!drawsInk(this.mode)) return null;
        var color = this.effectiveColor();
        current = {
          id: nextId++, slide: slide, mode: this.mode, size: this.size,
          colorIndex: color, points: [{ x: x, y: y, t: now() }]
        };
        list(slide).push(current);
        return current.id;
      },
      extend: function (x, y) {
        if (current) current.points.push({ x: x, y: y, t: now() });
      },
      end: function () {
        current = null;
      },

      // radius is in normalized units. Without aspect it applies per axis, so the
      // hit area is an ellipse on a non-square slide. With aspect (width / height)
      // x distances are scaled by it and radius is a fraction of the slide height,
      // which makes the hit area a circle in pixels.
      eraseAt: function (slide, x, y, radius, aspect) {
        var r = radius == null ? 0.02 : radius;
        var k = aspect > 0 ? aspect : 1;
        var removed = 0;
        bySlide[slide] = list(slide).filter(function (s) {
          if (s.mode === 'laser') return true;
          var hit = false;
          var pts = s.points;
          if (pts.length === 1) {
            hit = dist(x * k, y, pts[0].x * k, pts[0].y, pts[0].x * k, pts[0].y) <= r;
          }
          for (var i = 1; i < pts.length && !hit; i++) {
            hit = dist(x * k, y, pts[i - 1].x * k, pts[i - 1].y, pts[i].x * k, pts[i].y) <= r;
          }
          if (hit) removed++;
          return !hit;
        });
        return removed;
      },

      clear: function (slide) {
        bySlide[slide] = [];
      },

      showSlide: function (slide) {
        Object.keys(bySlide).forEach(function (k) {
          bySlide[k] = bySlide[k].filter(function (s) { return s.mode !== 'laser'; });
        });
        list(slide);
      },

      visible: function (slide) {
        var t = now();
        var out = [];
        prune(slide).forEach(function (s) {
          var pts = [];
          s.points.forEach(function (p) {
            var a = s.mode === 'laser' ? 1 - (t - p.t) / fadeMs : 1;
            if (a > 0) pts.push({ x: p.x, y: p.y, alpha: a });
          });
          if (pts.length) {
            out.push({ mode: s.mode, size: s.size, colorIndex: s.colorIndex, points: pts });
          }
        });
        return out;
      },

      animating: function (slide) {
        if (current) return true;
        var t = now();
        return list(slide).some(function (s) {
          return s.mode === 'laser' && alive(s, t);
        });
      }
    };
    return model;
  }

  // Distance from (px, py) to the segment (ax, ay)-(bx, by), normalized units.
  function dist(px, py, ax, ay, bx, by) {
    var dx = bx - ax;
    var dy = by - ay;
    var len2 = dx * dx + dy * dy;
    var u = len2 === 0 ? 0 : ((px - ax) * dx + (py - ay) * dy) / len2;
    u = Math.max(0, Math.min(1, u));
    var cx = ax + u * dx;
    var cy = ay + u * dy;
    return Math.sqrt((px - cx) * (px - cx) + (py - cy) * (py - cy));
  }

  function render(ctx, width, height, strokes) {
    ctx.clearRect(0, 0, width, height);
    (strokes || []).forEach(function (s) {
      var w = SIZES[s.size] * width / BASE_WIDTH;
      if (s.mode === 'highlighter') w *= HIGHLIGHTER_WIDTH_FACTOR;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.lineWidth = w;
      ctx.strokeStyle = PALETTE[s.colorIndex];
      var pts = s.points;
      if (s.mode === 'laser') {
        ctx.globalAlpha = pts.length ? pts[0].alpha : 1;
        if (pts.length === 1) segment(ctx, pts[0], pts[0], width, height);
        for (var i = 1; i < pts.length; i++) {
          ctx.globalAlpha = pts[i].alpha;
          segment(ctx, pts[i - 1], pts[i], width, height);
        }
      } else {
        ctx.globalAlpha = s.mode === 'highlighter' ? HIGHLIGHTER_ALPHA : 1;
        ctx.beginPath();
        ctx.moveTo(pts[0].x * width, pts[0].y * height);
        if (pts.length === 1) ctx.lineTo(pts[0].x * width, pts[0].y * height);
        for (var j = 1; j < pts.length; j++) {
          ctx.lineTo(pts[j].x * width, pts[j].y * height);
        }
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    });
  }

  function segment(ctx, a, b, width, height) {
    ctx.beginPath();
    ctx.moveTo(a.x * width, a.y * height);
    ctx.lineTo(b.x * width, b.y * height);
    ctx.stroke();
  }

  // CSS cursor value: a pen tip tinted with the palette colour, hotspot at the tip.
  function cursorFor(colorIndex, size) {
    var color = PALETTE[colorIndex] || PALETTE[0];
    var r = 2 + (SIZES[size] || SIZES[2]) / 4;
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
      + '<path d="M2 30 L6 20 L22 4 L28 10 L12 26 Z" fill="' + color + '" stroke="#333333" stroke-width="1.5" stroke-linejoin="round"/>'
      + '<circle cx="2" cy="30" r="' + r + '" fill="' + color + '" stroke="#333333" stroke-width="1"/>'
      + '</svg>';
    return 'url("data:image/svg+xml,' + encodeURIComponent(svg) + '") 2 30, crosshair';
  }

  // Lens diameter as a fraction of the slide height.
  var LENS_DIAMETER = 0.28;

  // Magnifier lens placement. rect is the slide box (viewport pixels), x/y the
  // pointer in 0..1 slide coordinates, canvasW/H the design canvas (1080 high).
  // left/top/size place the circle, clamped fully inside rect; tx/ty/scale
  // place the clone (origin top left) so the pointer's slide point sits at the
  // lens centre, even when the clamp moves the lens off the pointer.
  function lensGeometry(o) {
    var r = o.rect;
    var size = o.diameter > 0 ? o.diameter : r.height * LENS_DIAMETER;
    size = Math.max(0, Math.min(size, r.width, r.height));
    var px = r.left + o.x * r.width;
    var py = r.top + o.y * r.height;
    var left = Math.max(r.left, Math.min(r.left + r.width - size, px - size / 2));
    var top = Math.max(r.top, Math.min(r.top + r.height - size, py - size / 2));
    var scale = o.zoom * r.width / o.canvasW;
    return {
      left: left,
      top: top,
      size: size,
      tx: size / 2 - scale * o.x * o.canvasW,
      ty: size / 2 - scale * o.y * o.canvasH,
      scale: scale
    };
  }

  // --- DOM controller -------------------------------------------------------
  // Everything below touches the DOM only when called, never at load time.

  var MODE_LABELS = {
    laser: 'Laser', pen: 'Pen', highlighter: 'Highlighter', eraser: 'Eraser', magnifier: 'Magnifier'
  };
  var SIZE_LABELS = { 1: 'thin', 2: 'medium', 3: 'thick' };
  var MODE_CODES = { KeyP: 'laser', KeyO: 'pen', KeyI: 'highlighter', KeyU: 'eraser', KeyY: 'magnifier' };
  var BASE_HEIGHT = 1080;
  // Eraser radius in design pixels (1080-high slide) is the stroke width times this.
  var ERASER_FACTOR = 2;

  var surfaces = [];
  // deck-pen.css next to this script, for windows that must load it themselves.
  var cssHref = null;
  if (typeof document !== 'undefined' && document.currentScript && document.currentScript.src) {
    var src = document.currentScript.src;
    if (/deck-pen\.js(\?[^#]*)?(#.*)?$/.test(src)) {
      cssHref = src.replace(/deck-pen\.js(\?[^#]*)?(#.*)?$/, 'deck-pen.css');
    }
  }

  function isTypingTarget(target) {
    if (!target) return false;
    var tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
      Boolean(target.isContentEditable);
  }

  function consume(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  // The single controller shared by every surface (deck window, presenter preview).
  function createController(opts) {
    var model = createModel({ fadeMs: opts.fadeMs });
    var getSlide = opts.getSlide;
    var getSlideElement = opts.getSlideElement || function () { return null; };
    var getDeck = opts.getDeck || function () { return null; };
    var listeners = [];

    function emit() {
      listeners.slice().forEach(function (fn) { fn(controller); });
    }

    function redrawAll() {
      surfaces.forEach(function (s) { s.redraw(); });
    }

    // Each surface runs its own loop on its own window's requestAnimationFrame,
    // so a throttled deck window does not delay presenter frames (and back).
    function schedule() {
      surfaces.forEach(function (s) { s.schedule(); });
    }

    // A loop keeps running only while a pointer is down or laser ink is fading.
    function needsFrames() {
      return surfaces.some(function (s) { return s.isDrawing(); }) ||
        model.animating(getSlide());
    }

    function stopDrawing() {
      model.end();
      surfaces.forEach(function (s) { s.cancel(); });
    }

    function hideLens() {
      controller.lens.visible = false;
    }

    // Lens position in 0..1 slide coordinates; drawing it is left to the surfaces.
    function setLens(x, y, visible) {
      var lens = controller.lens;
      if (typeof x === 'number' && isFinite(x)) lens.x = Math.max(0, Math.min(1, x));
      if (typeof y === 'number' && isFinite(y)) lens.y = Math.max(0, Math.min(1, y));
      lens.visible = Boolean(visible);
      emit();
      schedule();
    }

    function setActive(on) {
      on = Boolean(on);
      if (on === controller.active) return;
      if (!on) {
        stopDrawing();
        hideLens();
      }
      controller.active = on;
      emit();
      schedule();
    }

    function selectMode(mode, toggles) {
      if (toggles && controller.active && model.mode === mode) {
        setActive(false);
        return;
      }
      model.end();
      if (!controller.active || model.mode !== mode) hideLens();
      model.setMode(mode);
      if (controller.active) emit();
      else setActive(true);
    }

    function chordAction(code) {
      if (MODE_CODES[code]) {
        return function () { selectMode(MODE_CODES[code], code === 'KeyP'); };
      }
      if (code === 'KeyT') {
        return function () {
          model.end();
          model.clear(getSlide());
          redrawAll();
        };
      }
      var digit = /^Digit([1-9])$/.exec(code || '');
      if (digit) {
        var n = Number(digit[1]);
        // In magnifier mode 1-3 pick the zoom and 4-9 do nothing (still consumed).
        return function () {
          if (model.mode === 'magnifier') {
            if (n > 3) return;
            model.setZoom(n + 1);
          } else if (n <= 3) {
            model.setSize(n);
          } else {
            model.setColor(n - 4);
          }
          emit();
        };
      }
      return null;
    }

    var controller = {
      model: model,
      active: false,
      lens: { x: 0.5, y: 0.5, visible: false },
      setLens: setLens,
      onChange: function (fn) {
        listeners.push(fn);
        return function () {
          var i = listeners.indexOf(fn);
          if (i >= 0) listeners.splice(i, 1);
        };
      },
      togglePen: function () { setActive(!controller.active); },
      setActive: setActive,
      // Consumes (preventDefault + stopImmediatePropagation) and returns true for
      // Option chords of the key map and for plain Esc while pen mode is on.
      handleKey: function (event) {
        if (isTypingTarget(event.target)) return false;
        if (event.ctrlKey || event.metaKey) return false;
        // Match Alt chords by code before the IME guard: on macOS Option+U and
        // Option+I are dead keys that Chromium may report as keyCode 229 or
        // isComposing. preventDefault() also suppresses the dead-key mark.
        if (event.altKey) {
          var action = chordAction(event.code);
          if (!action) return false;
          consume(event);
          if (!event.repeat) action();
          return true;
        }
        if (event.isComposing || event.keyCode === 229) return false;
        if (event.key === 'Escape' && controller.active) {
          consume(event);
          setActive(false);
          return true;
        }
        return false;
      },
      showSlide: function (slide) {
        stopDrawing();
        // A new slide hides the lens until the pointer moves again.
        hideLens();
        model.showSlide(slide);
        redrawAll();
      },
      currentSlide: function () { return getSlide(); },
      // Live element of the active slide and the live deck (the lens source).
      slideElement: function () { return getSlideElement(); },
      deckElement: function () { return getDeck(); },
      // Design canvas: 1080 high, width from the deck's ratio variables (the
      // same maths as PresenterView._canvasSize).
      canvasSize: function () {
        var deck = getDeck();
        var style = deck ? deck.ownerDocument.defaultView.getComputedStyle(deck) : null;
        var rw = style ? parseFloat(style.getPropertyValue('--slide-ratio-w')) : NaN;
        var rh = style ? parseFloat(style.getPropertyValue('--slide-ratio-h')) : NaN;
        if (!(rw > 0)) rw = 16;
        if (!(rh > 0)) rh = 9;
        return { w: Math.round(BASE_HEIGHT * rw / rh), h: BASE_HEIGHT };
      },
      redraw: redrawAll,
      schedule: schedule,
      needsFrames: needsFrames,
      surfaceCount: function () { return surfaces.length; }
    };
    return controller;
  }

  // Binds a canvas in any window to the shared controller. getRect() returns the
  // slide box in that window's viewport pixels. isPrimary also binds the keys.
  // Optional isInert() makes the canvas pointer-inert and refuse strokes while
  // it returns true (the deck window passes overview mode).
  function attachSurface(o) {
    var controller = api.controller;
    if (!controller) throw new Error('DeckPen controller is not initialised');
    var doc = o.doc;
    var win = doc.defaultView;
    var canvas = o.canvas;
    var ctx = canvas.getContext('2d');
    var pointerId = null;
    var frameId = null;
    var model = controller.model;

    function layout() {
      var r = o.getRect();
      canvas.style.left = r.left + 'px';
      canvas.style.top = r.top + 'px';
      canvas.style.width = r.width + 'px';
      canvas.style.height = r.height + 'px';
      var dpr = win.devicePixelRatio || 1;
      var w = Math.max(1, Math.round(r.width * dpr));
      var h = Math.max(1, Math.round(r.height * dpr));
      if (canvas.width !== w) canvas.width = w;
      if (canvas.height !== h) canvas.height = h;
    }

    function inert() {
      return Boolean(o.isInert && o.isInert());
    }

    function redraw() {
      sync();
      layout();
      render(ctx, canvas.width, canvas.height, model.visible(controller.currentSlide()));
      updateLens();
    }

    // --- Magnifier lens ------------------------------------------------
    // One lens per surface, created lazily next to the canvas in this
    // surface's document: div.rp-overlay-ui.rp-lens, inert, aria-hidden and
    // pointer-events none, never inside .slide. It holds a clone of the active
    // slide at design size, scaled so the pointer's slide point is at its
    // centre, plus a copy of this surface's pen canvas so ink is magnified too.
    // The clone is re-made on show, slide change, class changes in the active
    // slide (debounced) and resize, never per frame.
    // Limits of a DOM clone: canvas bitmaps are not cloned, so each source
    // canvas is copied with drawImage on this surface's frames while the lens
    // is visible (WebGL canvases only if their buffer is preserved). Iframes
    // are cloned as plain elements and reload; videos show their poster or
    // first frame and do not play.
    var lens = null;
    var lensShown = false;
    var lensDirty = true;
    var lensTimer = null;
    var lensObserver = null;

    function lensWanted() {
      if (!magnifying() || !controller.lens.visible || inert()) return false;
      var r = o.getRect();
      return r.width > 0 && r.height > 0;
    }

    function buildLens() {
      var el = doc.createElement('div');
      el.className = 'rp-overlay-ui rp-lens';
      el.setAttribute('inert', '');
      el.setAttribute('aria-hidden', 'true');
      el.hidden = true;
      var view = doc.createElement('div');
      view.className = 'rp-lens-view';
      var ink = doc.createElement('canvas');
      ink.className = 'rp-lens-ink';
      el.appendChild(view);
      canvas.parentNode.insertBefore(el, canvas.nextSibling);
      lens = { el: el, view: view, ink: ink, slide: null, size: null, sources: [], copies: [] };
    }

    // No ids, no scripts, no inline handlers, no autoplay, no radio grouping
    // with the live slide (a shared name would uncheck the live input).
    function neutralise(root) {
      var all = [root].concat(Array.prototype.slice.call(root.querySelectorAll('*')));
      all.forEach(function (el) {
        if (el.tagName === 'SCRIPT') {
          if (el.parentNode) el.parentNode.removeChild(el);
          return;
        }
        Array.prototype.slice.call(el.attributes).forEach(function (a) {
          var n = a.name.toLowerCase();
          if (n === 'id' || n === 'autofocus' || n === 'autoplay' || n.indexOf('on') === 0 ||
              (n === 'name' && el.tagName === 'INPUT')) {
            el.removeAttribute(a.name);
          }
        });
      });
    }

    function cloneSlide() {
      var slide = controller.slideElement();
      var size = controller.canvasSize();
      lens.view.textContent = '';
      lens.view.style.width = size.w + 'px';
      lens.view.style.height = size.h + 'px';
      lens.slide = slide;
      lens.size = size;
      lens.sources = [];
      lens.copies = [];
      lensDirty = false;
      if (!slide) return;

      var liveDeck = controller.deckElement();
      var wrap = doc.createElement('div');
      if (liveDeck) {
        wrap.className = Array.prototype.filter.call(liveDeck.classList, function (name) {
          return name !== 'overview-mode';
        }).join(' ');
        if (liveDeck.hasAttribute('data-fit')) wrap.setAttribute('data-fit', liveDeck.getAttribute('data-fit'));
        if (liveDeck.lang) wrap.lang = liveDeck.lang;
      }
      wrap.classList.add('slide-deck');

      var clone = doc.importNode(slide, true);
      neutralise(clone);
      Array.prototype.slice.call(clone.classList).forEach(function (name) {
        if (name === 'leaving' || name === 'entering' || name.indexOf('transition-') === 0) {
          clone.classList.remove(name);
        }
      });
      clone.classList.add('active');
      wrap.appendChild(clone);
      lens.view.appendChild(wrap);
      lens.view.appendChild(lens.ink);
      lens.sources = Array.prototype.slice.call(slide.querySelectorAll('canvas'));
      lens.copies = Array.prototype.slice.call(clone.querySelectorAll('canvas'));
      watchSlide(slide);
    }

    function watchSlide(slide) {
      if (lensObserver) lensObserver.disconnect();
      lensObserver = new MutationObserver(queueReclone);
      lensObserver.observe(slide, { attributes: true, attributeFilter: ['class'], subtree: true });
    }

    // Fragment reveals and other class changes settle before one re-clone.
    function queueReclone() {
      clearTimeout(lensTimer);
      lensTimer = setTimeout(function () {
        lensTimer = null;
        lensDirty = true;
        if (lensShown) redraw();
      }, 50);
    }

    function hideLensEl() {
      lensShown = false;
      lensDirty = true;
      clearTimeout(lensTimer);
      lensTimer = null;
      if (lensObserver) {
        lensObserver.disconnect();
        lensObserver = null;
      }
      if (!lens) return;
      lens.el.hidden = true;
      // Drop the clone so no hidden copy of the slide stays in the document.
      lens.view.textContent = '';
      lens.slide = null;
      lens.sources = [];
      lens.copies = [];
    }

    function copyCanvas(src, dst) {
      if (dst.width !== src.width) dst.width = src.width;
      if (dst.height !== src.height) dst.height = src.height;
      try {
        var g = dst.getContext('2d');
        g.clearRect(0, 0, dst.width, dst.height);
        if (src.width && src.height) g.drawImage(src, 0, 0);
      } catch (e) { /* a canvas that cannot be drawn stays blank in the lens */ }
    }

    function updateLens() {
      if (!lensWanted()) {
        if (lensShown) hideLensEl();
        return;
      }
      if (!lens) buildLens();
      if (!lensShown || lensDirty || controller.slideElement() !== lens.slide) cloneSlide();
      var g = lensGeometry({
        rect: o.getRect(), x: controller.lens.x, y: controller.lens.y, zoom: model.zoom,
        canvasW: lens.size.w, canvasH: lens.size.h
      });
      var st = lens.el.style;
      st.left = g.left + 'px';
      st.top = g.top + 'px';
      st.width = g.size + 'px';
      st.height = g.size + 'px';
      lens.view.style.transform = 'translate(' + g.tx + 'px, ' + g.ty + 'px) scale(' + g.scale + ')';
      lens.el.hidden = false;
      lensShown = true;
      copyCanvas(canvas, lens.ink);
      for (var i = 0; i < lens.sources.length; i++) {
        if (lens.copies[i]) copyCanvas(lens.sources[i], lens.copies[i]);
      }
    }

    // Source canvases may animate, so they are copied every frame while shown.
    function lensNeedsFrames() {
      return lensShown && lens.sources.length > 0;
    }

    // Mode, zoom and visibility changes: hide at once, or draw on the next frame.
    function onLensChange() {
      if (lensShown && !lensWanted()) hideLensEl();
      else if (lensShown || lensWanted()) schedule();
    }

    function onResize() {
      if (lensShown) queueReclone();
    }

    function point(event) {
      var r = o.getRect();
      return {
        x: (event.clientX - r.left) / r.width,
        y: (event.clientY - r.top) / r.height,
        aspect: r.width / r.height
      };
    }

    function apply(event, starting) {
      var p = point(event);
      var slide = controller.currentSlide();
      if (model.mode === 'eraser') {
        var radius = SIZES[model.size] * ERASER_FACTOR / BASE_HEIGHT;
        model.eraseAt(slide, p.x, p.y, radius, p.aspect);
      } else if (starting) {
        model.begin(slide, p.x, p.y);
      } else {
        model.extend(p.x, p.y);
      }
    }

    function sync() {
      var off = inert();
      if (off) finish();
      canvas.classList.toggle('active', controller.active && !off);
      if (model.mode === 'eraser') canvas.style.cursor = 'cell';
      else if (model.mode === 'magnifier') canvas.style.cursor = 'crosshair';
      else canvas.style.cursor = cursorFor(model.effectiveColor(), model.size);
    }

    function magnifying() {
      return controller.active && model.mode === 'magnifier';
    }

    function onDown(event) {
      // Magnifier mode only tracks the pointer: no stroke, no capture.
      if (!controller.active || inert() || pointerId !== null || model.mode === 'magnifier') return;
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      event.preventDefault();
      pointerId = event.pointerId;
      try { canvas.setPointerCapture(pointerId); } catch (e) { /* synthetic pointer */ }
      apply(event, true);
      controller.redraw();
      controller.schedule();
    }

    function onMove(event) {
      if (pointerId === null && magnifying()) {
        if (inert()) return;
        var p = point(event);
        controller.setLens(p.x, p.y, true);
        return;
      }
      if (event.pointerId !== pointerId) return;
      apply(event, false);
    }

    function onLeave() {
      if (magnifying() && controller.lens.visible) controller.setLens(null, null, false);
    }

    function onUp(event) {
      if (event.type === 'pointercancel' && pointerId === null) onLeave();
      if (event.pointerId !== pointerId) return;
      if (event.type === 'pointerup') apply(event, false);
      finish();
      controller.redraw();
      controller.schedule();
    }

    function finish() {
      if (pointerId === null) return;
      var id = pointerId;
      pointerId = null;
      model.end();
      try {
        if (canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
      } catch (e) { /* already released */ }
    }

    function onKey(event) { controller.handleKey(event); }

    function frame() {
      frameId = null;
      redraw();
      if (controller.needsFrames() || lensNeedsFrames()) schedule();
    }

    function schedule() {
      if (frameId === null) frameId = win.requestAnimationFrame(frame);
    }

    var surface = {
      redraw: redraw,
      schedule: schedule,
      isDrawing: function () { return pointerId !== null; },
      cancel: finish
    };

    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointercancel', onUp);
    canvas.addEventListener('lostpointercapture', onUp);
    canvas.addEventListener('pointerleave', onLeave);
    win.addEventListener('resize', redraw);
    win.addEventListener('resize', onResize);
    if (o.isPrimary) win.addEventListener('keydown', onKey, true);
    var unsubscribe = controller.onChange(sync);
    var unsubscribeLens = controller.onChange(onLensChange);
    surfaces.push(surface);
    sync();
    redraw();

    return {
      redraw: redraw,
      destroy: function () {
        finish();
        if (frameId !== null) {
          try { win.cancelAnimationFrame(frameId); } catch (e) { /* window closed */ }
          frameId = null;
        }
        canvas.removeEventListener('pointerdown', onDown);
        canvas.removeEventListener('pointermove', onMove);
        canvas.removeEventListener('pointerup', onUp);
        canvas.removeEventListener('pointercancel', onUp);
        canvas.removeEventListener('lostpointercapture', onUp);
        canvas.removeEventListener('pointerleave', onLeave);
        win.removeEventListener('resize', redraw);
        win.removeEventListener('resize', onResize);
        if (o.isPrimary) win.removeEventListener('keydown', onKey, true);
        unsubscribe();
        unsubscribeLens();
        hideLensEl();
        if (lens && lens.el.parentNode) lens.el.parentNode.removeChild(lens.el);
        lens = null;
        var i = surfaces.indexOf(surface);
        if (i >= 0) surfaces.splice(i, 1);
      }
    };
  }

  // Turns el (in any document) into the mode badge; update(show) refreshes it
  // from the shared controller.
  function buildBadge(el) {
    var doc = el.ownerDocument;
    el.classList.add('rp-overlay-ui', 'rp-pen-badge');
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    el.hidden = true;
    var swatch = doc.createElement('span');
    swatch.className = 'rp-pen-swatch';
    swatch.setAttribute('aria-hidden', 'true');
    var label = doc.createElement('span');
    label.className = 'rp-pen-label';
    el.appendChild(swatch);
    el.appendChild(label);
    return {
      el: el,
      update: function (show) {
        var model = api.controller.model;
        el.hidden = !show;
        var magnifier = model.mode === 'magnifier';
        label.textContent = magnifier
          ? MODE_LABELS.magnifier + ' ' + model.zoom + 'x'
          : MODE_LABELS[model.mode] + ', ' + SIZE_LABELS[model.size];
        swatch.hidden = model.mode === 'eraser';
        // The magnifier shows a neutral swatch (theme colour) instead of ink.
        swatch.classList.toggle('rp-pen-swatch-neutral', magnifier);
        swatch.style.backgroundColor = magnifier ? '' : PALETTE[model.effectiveColor()];
      }
    };
  }

  // Deck window: body-level canvas over the deck box plus the mode badge.
  function initDeck(framework, deck) {
    if (api.controller) return;
    var overlay = window.DeckOverlay;
    var penOpts = framework.pen || {};
    var controller = createController({
      fadeMs: penOpts.fadeMs,
      getSlide: function () { return framework.currentSlide; },
      getSlideElement: function () { return framework.slides[framework.currentSlide] || null; },
      getDeck: function () { return deck; }
    });
    api.controller = controller;

    var canvas = overlay.makeOverlay('canvas', 'rp-pen-canvas');
    canvas.classList.add('rp-pen-canvas');
    canvas.setAttribute('aria-hidden', 'true');

    var badge = overlay.makeOverlay('div', 'rp-pen-badge');
    var badgeUi = buildBadge(badge);

    function deckRect() { return deck.getBoundingClientRect(); }

    function placeBadge() {
      var r = deckRect();
      badge.style.left = r.left + 'px';
      badge.style.top = r.top + 'px';
    }

    function syncBadge() {
      badgeUi.update(controller.active && penOpts.audienceBadge !== false);
      placeBadge();
    }

    var surface = attachSurface({
      doc: document, canvas: canvas, getRect: deckRect, isPrimary: true,
      isInert: function () { return deck.classList.contains('overview-mode'); }
    });
    controller.onChange(syncBadge);
    syncBadge();
    // The deck scale lives in the deck's inline style; overview mode in its class.
    new MutationObserver(function () {
      surface.redraw();
      placeBadge();
    }).observe(deck, { attributes: true, attributeFilter: ['style', 'class'] });
    window.addEventListener('resize', placeBadge);
  }

  var api = {
    MODES: MODES, SIZES: SIZES, ZOOMS: ZOOMS, PALETTE: PALETTE,
    HIGHLIGHTER_ALPHA: HIGHLIGHTER_ALPHA,
    HIGHLIGHTER_WIDTH_FACTOR: HIGHLIGHTER_WIDTH_FACTOR,
    createModel: createModel, render: render, cursorFor: cursorFor,
    lensGeometry: lensGeometry, LENS_DIAMETER: LENS_DIAMETER,
    attachSurface: attachSurface, buildBadge: buildBadge,
    cssHref: cssHref,
    controller: null
  };
  if (typeof window !== 'undefined') {
    window.DeckPen = window.DeckPen || api;
    if (window.DeckPen === api && window.DeckOverlay) {
      window.DeckOverlay.register('pen', {
        priority: 0,
        init: initDeck,
        slideChange: function () {
          if (api.controller) api.controller.showSlide(api.controller.currentSlide());
        }
      });
    }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
