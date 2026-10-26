/* deck-pen.js - pen mode ink model, canvas renderer and cursor helper.
 * Pure core: no DOM access at load time. Coordinates are 0..1 of the slide box. */
(function () {
  'use strict';

  var MODES = ['laser', 'pen', 'highlighter', 'eraser'];
  var SIZES = { 1: 4, 2: 8, 3: 16 };
  var PALETTE = ['#e53935', '#fdd835', '#43a047', '#1e88e5', '#ffffff', '#000000'];
  var HIGHLIGHTER_ALPHA = 0.35;
  var HIGHLIGHTER_WIDTH_FACTOR = 3;
  var HIGHLIGHTER_DEFAULT_COLOR = 1;
  var BASE_WIDTH = 1920;

  function createModel(opts) {
    opts = opts || {};
    var fadeMs = opts.fadeMs == null ? 3000 : opts.fadeMs;
    var now = opts.now || function () { return Date.now(); };
    var bySlide = {};
    var current = null;
    var colorChosen = false;
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
      colorIndex: 0,

      setMode: function (name) {
        if (MODES.indexOf(name) >= 0) this.mode = name;
      },
      setSize: function (n) {
        if (Object.prototype.hasOwnProperty.call(SIZES, n)) this.size = Number(n);
      },
      setColor: function (i) {
        if (typeof i === 'number' && i % 1 === 0 && i >= 0 && i < PALETTE.length) {
          this.colorIndex = i;
          colorChosen = true;
        }
      },

      begin: function (slide, x, y) {
        var color = this.mode === 'highlighter' && !colorChosen
          ? HIGHLIGHTER_DEFAULT_COLOR : this.colorIndex;
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

      eraseAt: function (slide, x, y, radius) {
        var r = radius == null ? 0.02 : radius;
        var removed = 0;
        bySlide[slide] = list(slide).filter(function (s) {
          if (s.mode === 'laser') return true;
          var hit = false;
          var pts = s.points;
          if (pts.length === 1) {
            hit = dist(x, y, pts[0].x, pts[0].y, pts[0].x, pts[0].y) <= r;
          }
          for (var i = 1; i < pts.length && !hit; i++) {
            hit = dist(x, y, pts[i - 1].x, pts[i - 1].y, pts[i].x, pts[i].y) <= r;
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

  var api = {
    MODES: MODES, SIZES: SIZES, PALETTE: PALETTE,
    HIGHLIGHTER_ALPHA: HIGHLIGHTER_ALPHA,
    HIGHLIGHTER_WIDTH_FACTOR: HIGHLIGHTER_WIDTH_FACTOR,
    createModel: createModel, render: render, cursorFor: cursorFor
  };
  if (typeof window !== 'undefined') window.DeckPen = window.DeckPen || api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
