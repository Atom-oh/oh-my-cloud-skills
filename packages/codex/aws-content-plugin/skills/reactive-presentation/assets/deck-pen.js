/* deck-pen.js - pen mode ink model, canvas renderer, cursor helper and the
 * deck-window controller (overlay module 'pen'). No DOM access at load time.
 * Coordinates are 0..1 of the slide box. */
(function () {
  'use strict';

  var MODES = ['laser', 'pen', 'highlighter', 'eraser'];
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
    // One chosen colour per drawing mode; the eraser has none and shows the last drawing mode's.
    var colors = { laser: DEFAULT_COLORS.laser, pen: DEFAULT_COLORS.pen, highlighter: DEFAULT_COLORS.highlighter };
    var lastDrawMode = 'laser';
    var nextId = 1;

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
      // Read-only view of the colour the current mode uses.
      get colorIndex() { return this.effectiveColor(); },

      setMode: function (name) {
        if (MODES.indexOf(name) < 0) return;
        this.mode = name;
        if (name !== 'eraser') lastDrawMode = name;
      },
      setSize: function (n) {
        if (Object.prototype.hasOwnProperty.call(SIZES, n)) this.size = Number(n);
      },
      setColor: function (i) {
        if (this.mode === 'eraser') return;
        if (typeof i === 'number' && i % 1 === 0 && i >= 0 && i < PALETTE.length) {
          colors[this.mode] = i;
        }
      },

      // Palette index the current mode draws with (each drawing mode keeps its own).
      effectiveColor: function () {
        return colors[this.mode === 'eraser' ? lastDrawMode : this.mode];
      },

      // Returns the new stroke id, or null in eraser mode (no stroke is created).
      begin: function (slide, x, y) {
        if (this.mode === 'eraser') return null;
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

  // --- DOM controller -------------------------------------------------------
  // Everything below touches the DOM only when called, never at load time.

  var MODE_LABELS = { laser: 'Laser', pen: 'Pen', highlighter: 'Highlighter', eraser: 'Eraser' };
  var SIZE_LABELS = { 1: 'thin', 2: 'medium', 3: 'thick' };
  var MODE_CODES = { KeyP: 'laser', KeyO: 'pen', KeyI: 'highlighter', KeyU: 'eraser' };
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

    function setActive(on) {
      on = Boolean(on);
      if (on === controller.active) return;
      if (!on) stopDrawing();
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
      model.setMode(mode);
      if (controller.active) emit();
      else setActive(true);
    }

    function chordAction(code) {
      if (MODE_CODES[code]) {
        return function () { selectMode(MODE_CODES[code], code === 'KeyP'); };
      }
      if (code === 'KeyY') {
        return function () {
          model.end();
          model.clear(getSlide());
          redrawAll();
        };
      }
      var digit = /^Digit([1-9])$/.exec(code || '');
      if (digit) {
        var n = Number(digit[1]);
        return function () {
          if (n <= 3) model.setSize(n);
          else model.setColor(n - 4);
          emit();
        };
      }
      return null;
    }

    var controller = {
      model: model,
      active: false,
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
        model.showSlide(slide);
        redrawAll();
      },
      currentSlide: function () { return getSlide(); },
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
      canvas.style.cursor = model.mode === 'eraser'
        ? 'cell' : cursorFor(model.effectiveColor(), model.size);
    }

    function onDown(event) {
      if (!controller.active || inert() || pointerId !== null) return;
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      event.preventDefault();
      pointerId = event.pointerId;
      try { canvas.setPointerCapture(pointerId); } catch (e) { /* synthetic pointer */ }
      apply(event, true);
      controller.redraw();
      controller.schedule();
    }

    function onMove(event) {
      if (event.pointerId !== pointerId) return;
      apply(event, false);
    }

    function onUp(event) {
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
      if (controller.needsFrames()) schedule();
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
    win.addEventListener('resize', redraw);
    if (o.isPrimary) win.addEventListener('keydown', onKey, true);
    var unsubscribe = controller.onChange(sync);
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
        win.removeEventListener('resize', redraw);
        if (o.isPrimary) win.removeEventListener('keydown', onKey, true);
        unsubscribe();
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
        label.textContent = MODE_LABELS[model.mode] + ', ' + SIZE_LABELS[model.size];
        swatch.hidden = model.mode === 'eraser';
        swatch.style.backgroundColor = PALETTE[model.effectiveColor()];
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
      getSlide: function () { return framework.currentSlide; }
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
    MODES: MODES, SIZES: SIZES, PALETTE: PALETTE,
    HIGHLIGHTER_ALPHA: HIGHLIGHTER_ALPHA,
    HIGHLIGHTER_WIDTH_FACTOR: HIGHLIGHTER_WIDTH_FACTOR,
    createModel: createModel, render: render, cursorFor: cursorFor,
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
