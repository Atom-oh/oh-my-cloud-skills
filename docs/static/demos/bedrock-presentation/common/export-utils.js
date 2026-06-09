/**
 * Export Utilities for Reactive Presentation
 * PDF export (via browser print) and ZIP download (via JSZip CDN).
 * Include in TOC index.html pages: <script src="../common/export-utils.js"></script>
 */
const ExportUtils = {
  JSZIP_CDN: 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',
  PPTXGEN_CDN: 'https://cdn.jsdelivr.net/gh/gitbrent/PptxGenJS@3.12.0/dist/pptxgen.bundle.js',
  HTML2CANVAS_CDN: 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',

  /** Escape HTML special characters to prevent XSS in generated markup */
  _escapeHTML: function(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },

  /** Image file extensions to include in ZIP */
  _IMAGE_EXTS: /\.(svg|png|jpg|jpeg|gif|webp|ico)$/i,

  /**
   * Extract referenced image URLs from an HTML string.
   * Scans for <img src>, CSS url(), and JS .src assignments.
   * Returns deduplicated array of relative image paths.
   */
  _extractImageURLs: function(html) {
    var urls = new Set();
    var match;

    // Pattern 1: <img ... src="PATH" ...>
    var imgSrc = /<img[^>]+src\s*=\s*["']([^"']+)["']/gi;
    while ((match = imgSrc.exec(html)) !== null) urls.add(match[1]);

    // Pattern 2: url('PATH') or url(PATH) — CSS backgrounds
    var cssUrl = /url\(\s*['"]?([^'")]+)['"]?\s*\)/gi;
    while ((match = cssUrl.exec(html)) !== null) urls.add(match[1]);

    // Pattern 3: .src = 'PATH' or .src = "PATH" — JS image loading
    var jsSrc = /\.src\s*=\s*['"]([^'"]+)['"]/gi;
    while ((match = jsSrc.exec(html)) !== null) urls.add(match[1]);

    // Filter: keep only relative paths to image files, exclude data URIs and absolute URLs
    var imageExts = this._IMAGE_EXTS;
    return Array.from(urls).filter(function(u) {
      if (u.indexOf('data:') === 0 || u.indexOf('http://') === 0 || u.indexOf('https://') === 0 || u.indexOf('//') === 0) return false;
      return imageExts.test(u);
    });
  },

  COMMON_FILES: [
    'theme.css', 'theme-override.css', 'slide-framework.js',
    'presenter-view.js', 'animation-utils.js', 'quiz-component.js',
    'export-utils.js'
  ],

  /** Discover block HTML files from .block-card anchor links on the current page */
  getBlockFiles: function() {
    return Array.from(document.querySelectorAll('a.block-card'))
      .map(function(a) { return a.getAttribute('href'); })
      .filter(Boolean);
  },

  /** Get presentation slug from current URL path */
  getSlug: function() {
    var parts = window.location.pathname.replace(/\/index\.html$/, '').split('/').filter(Boolean);
    return parts[parts.length - 1] || 'presentation';
  },

  _resolveCommonPath: function() {
    var tags = document.querySelectorAll('link[href*="common/"], script[src*="common/"]');
    for (var i = 0; i < tags.length; i++) {
      var attr = tags[i].getAttribute('href') || tags[i].getAttribute('src') || '';
      var idx = attr.indexOf('common/');
      if (idx !== -1) return attr.substring(0, idx + 7);
    }
    return './common/';
  },

  /**
   * Export all slides as PDF via browser print dialog.
   * Fetches all block HTML files, extracts slides, opens a print-optimized view.
   * @param {Object} options - { title: string }
   */
  exportPDF: async function(options) {
    options = options || {};
    var title = options.title || document.title;
    var blocks = options.blocks || this.getBlockFiles();
    if (!blocks.length) { alert('No block files found on this page.'); return; }

    this.showProgress('Preparing PDF export...');

    try {
      var responses = await Promise.all(
        blocks.map(function(file, i) {
          ExportUtils.updateProgress('Fetching ' + file + '...', ((i + 1) / blocks.length) * 50);
          return fetch(file).then(function(r) {
            if (!r.ok) throw new Error('Failed to fetch ' + file + ': ' + r.status);
            return r.text();
          });
        })
      );

      var allStyles = '';
      var allSlides = '';
      var slideCount = 0;

      responses.forEach(function(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        doc.querySelectorAll('style').forEach(function(s) { allStyles += s.textContent + '\n'; });
        doc.querySelectorAll('.slide').forEach(function(slide) {
          slideCount++;
          allSlides += '<div class="slide print-slide">' + slide.innerHTML + '</div>\n';
        });
      });

      this.updateProgress('Building print view (' + slideCount + ' slides)...', 75);

      var baseURL = window.location.href;
      var commonPath = this._resolveCommonPath();
      var printHTML = '<!DOCTYPE html>\n<html lang="ko">\n<head>\n' +
        '<meta charset="UTF-8">\n' +
        '<base href="' + this._escapeHTML(baseURL) + '">\n' +
        '<title>' + this._escapeHTML(title) + ' - PDF Export</title>\n' +
        '<link rel="stylesheet" href="' + commonPath + 'theme.css">\n' +
        '<link rel="stylesheet" href="' + commonPath + 'theme-override.css">\n' +
        '<style>\n' +
        '@page { size: 16in 9in landscape; margin: 0; }\n' +
        'html, body { margin: 0; padding: 0; background: #000; overflow: visible !important; display: block !important; height: auto !important; }\n' +
        '.print-slide {\n' +
        '  width: 16in; height: 9in;\n' +
        '  display: flex !important; flex-direction: column;\n' +
        '  padding: 2rem 2.7rem;\n' +
        '  background: var(--bg-primary);\n' +
        '  position: relative;\n' +
        '  page-break-after: always;\n' +
        '  overflow: hidden;\n' +
        '  box-sizing: border-box;\n' +
        '}\n' +
        '.print-slide:last-child { page-break-after: auto; }\n' +
        'canvas { display: none !important; }\n' +
        '.canvas-container { position: relative; }\n' +
        '.canvas-container::after {\n' +
        '  content: "[Interactive Animation]";\n' +
        '  display: flex; align-items: center; justify-content: center;\n' +
        '  width: 100%; min-height: 200px;\n' +
        '  color: var(--text-muted); font-style: italic; font-size: 1.1rem;\n' +
        '  background: var(--bg-secondary); border-radius: 0.5rem;\n' +
        '}\n' +
        '.canvas-controls { display: none !important; }\n' +
        '.progress-bar, .slide-counter, .nav-hint, .slide-logo, .slide-footer { display: none !important; }\n' +
        allStyles + '\n' +
        '</style>\n' +
        '</head>\n<body>\n' +
        allSlides +
        '<script>window.onload = function() { setTimeout(function() { window.print(); }, 500); };<\/script>\n' +
        '</body>\n</html>';

      this.updateProgress('Opening print dialog...', 95);

      var printWindow = window.open('', '_blank');
      if (!printWindow) {
        this.hideProgress();
        alert('Pop-up blocked. Please allow pop-ups for this site and try again.');
        return;
      }
      printWindow.document.write(printHTML);
      printWindow.document.close();

      this.hideProgress();
    } catch (err) {
      this.hideProgress();
      alert('PDF export failed: ' + err.message);
      console.error('PDF export error:', err);
    }
  },

  /**
   * Download all presentation files as a ZIP archive.
   * Includes block HTMLs, TOC page, common framework files, and all referenced images.
   * Images are discovered by scanning HTML content for <img src>, CSS url(), and JS .src patterns.
   * @param {Object} options - { slug: string }
   */
  downloadZIP: async function(options) {
    options = options || {};
    var slug = options.slug || this.getSlug();
    var blocks = options.blocks || this.getBlockFiles();
    if (!blocks.length) { alert('No block files found on this page.'); return; }

    this.showProgress('Preparing ZIP download...');

    try {
      this.updateProgress('Loading JSZip library...', 5);
      await this.loadJSZip();

      var zip = new JSZip();
      var slugFolder = zip.folder(slug);
      var commonFolder = zip.folder('common');
      var imageURLs = new Set();
      var fetched = 0;
      var totalFiles = blocks.length + this.COMMON_FILES.length + 1;

      // Fetch block HTML files and scan for referenced images
      var blockHTMLs = [];
      for (var i = 0; i < blocks.length; i++) {
        var file = blocks[i];
        this.updateProgress('Fetching ' + file + '...', 10 + (fetched / totalFiles) * 40);
        var resp = await fetch(file);
        if (resp.ok) {
          var html = await resp.text();
          slugFolder.file(file, html);
          blockHTMLs.push(html);
        }
        fetched++;
      }

      // Fetch TOC index.html (current page) and scan for images
      this.updateProgress('Fetching index.html...', 10 + (fetched / totalFiles) * 40);
      var tocResp = await fetch('index.html');
      var tocHTML = '';
      if (tocResp.ok) {
        tocHTML = await tocResp.text();
        slugFolder.file('index.html', tocHTML);
      }
      fetched++;

      // Fetch common framework files and scan theme-override.css for images
      var themeOverrideCSS = '';
      for (var j = 0; j < this.COMMON_FILES.length; j++) {
        var cFile = this.COMMON_FILES[j];
        this.updateProgress('Fetching common/' + cFile + '...', 10 + (fetched / totalFiles) * 40);
        try {
          var cResp = await fetch('../common/' + cFile);
          if (cResp.ok) {
            var cText = await cResp.text();
            commonFolder.file(cFile, cText);
            if (cFile === 'theme-override.css') themeOverrideCSS = cText;
          }
        } catch (e) { /* skip missing optional files */ }
        fetched++;
      }

      // Scan all fetched HTML/CSS content for referenced image URLs
      this.updateProgress('Scanning for referenced images...', 55);
      var self = this;
      blockHTMLs.forEach(function(html) {
        // Block HTML paths are relative to the slug dir (e.g., ../common/aws-icons/...)
        self._extractImageURLs(html).forEach(function(u) { imageURLs.add(u); });
      });
      this._extractImageURLs(tocHTML).forEach(function(u) { imageURLs.add(u); });
      // theme-override.css lives in common/, so paths are relative to common/ (e.g., pptx-theme/images/...)
      this._extractImageURLs(themeOverrideCSS).forEach(function(u) {
        // Normalize to ../common/ relative form to match block HTML paths
        if (u.indexOf('../') !== 0 && u.indexOf('./') !== 0) {
          imageURLs.add('../common/' + u);
        } else {
          imageURLs.add(u);
        }
      });

      // Fetch discovered images and add to ZIP
      var imageList = Array.from(imageURLs);
      var imgFetched = 0;
      for (var k = 0; k < imageList.length; k++) {
        var imgURL = imageList[k];
        this.updateProgress('Fetching image ' + (k + 1) + '/' + imageList.length + '...', 58 + (imgFetched / Math.max(imageList.length, 1)) * 20);
        try {
          var imgResp = await fetch(imgURL);
          if (imgResp.ok) {
            // Resolve ../common/path/to/img → common/path/to/img in ZIP
            var zipPath = imgURL.replace(/^\.\.\//g, '');
            zip.file(zipPath, await imgResp.blob());
          }
        } catch (e) { /* skip unreachable images */ }
        imgFetched++;
      }

      this.updateProgress('Generating ZIP archive...', 80);

      var blob = await zip.generateAsync({ type: 'blob' }, function(metadata) {
        ExportUtils.updateProgress('Compressing... ' + Math.round(metadata.percent) + '%', 80 + (metadata.percent / 100) * 15);
      });

      // Trigger browser download
      this.updateProgress('Starting download...', 98);
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = slug + '.zip';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      this.hideProgress();
    } catch (err) {
      this.hideProgress();
      alert('ZIP download failed: ' + err.message);
      console.error('ZIP download error:', err);
    }
  },

  /** Lazy-load JSZip from CDN */
  loadJSZip: function() {
    if (window.JSZip) return Promise.resolve();
    return new Promise(function(resolve, reject) {
      var script = document.createElement('script');
      script.src = ExportUtils.JSZIP_CDN;
      script.onload = resolve;
      script.onerror = function() { reject(new Error('Failed to load JSZip from CDN')); };
      document.head.appendChild(script);
    });
  },

  /** Lazy-load PptxGenJS from CDN */
  loadPptxGen: function() {
    if (window.PptxGenJS) return Promise.resolve();
    return new Promise(function(resolve, reject) {
      var script = document.createElement('script');
      script.src = ExportUtils.PPTXGEN_CDN;
      script.onload = resolve;
      script.onerror = function() { reject(new Error('Failed to load PptxGenJS from CDN')); };
      document.head.appendChild(script);
    });
  },

  /** Lazy-load html2canvas from CDN */
  loadHtml2Canvas: function() {
    if (window.html2canvas) return Promise.resolve();
    return new Promise(function(resolve, reject) {
      var script = document.createElement('script');
      script.src = ExportUtils.HTML2CANVAS_CDN;
      script.onload = resolve;
      script.onerror = function() { reject(new Error('Failed to load html2canvas from CDN')); };
      document.head.appendChild(script);
    });
  },

  /**
   * Load a block HTML file into a hidden iframe and wait for full rendering.
   * Returns the iframe's contentDocument with all CSS/JS applied.
   */
  _loadBlockInIframe: function(blockUrl) {
    return new Promise(function(resolve, reject) {
      var iframe = document.createElement('iframe');
      iframe.style.cssText = 'position:fixed;left:-9999px;top:0;width:1920px;height:1080px;border:none;opacity:0;pointer-events:none;';
      document.body.appendChild(iframe);

      iframe.onload = function() {
        // Wait for images and fonts to load
        var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        var checkReady = function() {
          // Give scripts time to execute (canvas rendering, etc.)
          setTimeout(function() { resolve({ doc: iframeDoc, iframe: iframe }); }, 800);
        };

        if (iframeDoc.readyState === 'complete') {
          checkReady();
        } else {
          iframe.contentWindow.addEventListener('load', checkReady);
        }
      };
      iframe.onerror = function() {
        document.body.removeChild(iframe);
        reject(new Error('Failed to load ' + blockUrl));
      };

      // Resolve relative URL against current page
      var baseUrl = window.location.href.replace(/[^/]*$/, '');
      iframe.src = new URL(blockUrl, baseUrl).href;
    });
  },

  /**
   * Reveal all fragments and complete all canvas steps in a document.
   * This puts every slide into its "finished" visual state.
   */
  _completeAllAnimations: function(doc) {
    // 1. Reveal all fragments
    doc.querySelectorAll('.fragment').forEach(function(el) {
      el.classList.add('visible');
    });

    // 2. Complete all canvas step animations
    doc.querySelectorAll('.slide').forEach(function(slide) {
      // Advance __canvasStep to MAX_STEP
      if (slide.__canvasStep) {
        var maxStep = parseInt(slide.dataset.canvasMaxStep || '20', 10);
        for (var s = 0; s < maxStep; s++) {
          var result = slide.__canvasStep('next');
          if (result === false) break;
        }
      }

      // Show all tab panels (capture the active one)
      // Show all compare sections
    });

    // 3. Make all slides visible for capture (override framework's active logic)
    doc.querySelectorAll('.slide').forEach(function(slide) {
      slide.style.display = 'flex';
      slide.style.opacity = '1';
      slide.style.visibility = 'visible';
      slide.style.position = 'relative';
      slide.style.transform = 'none';
    });
  },

  /**
   * Extract theme info from a block HTML for PPTX metadata.
   * Reads __remarpTheme and CSS custom properties.
   */
  _extractThemeFromBlock: async function(blockFile) {
    var info = { bgColor: null, footerText: null, fonts: {} };
    try {
      var resp = await fetch(blockFile);
      if (!resp.ok) return info;
      var html = await resp.text();

      // Extract __remarpTheme JSON
      var themeMatch = html.match(/window\.__remarpTheme\s*=\s*(\{[^;]+\})/);
      if (themeMatch) {
        var theme = JSON.parse(themeMatch[1]);
        if (theme.footer) info.footerText = theme.footer;
        if (theme.fonts) info.fonts = theme.fonts;

        // Derive background color from theme colors (darkest of dk1/dk2/lt1/lt2)
        var colors = theme.colors || {};
        var darkest = null;
        var darkestLum = 1;
        ['dk1', 'dk2', 'lt1', 'lt2'].forEach(function(k) {
          if (!colors[k]) return;
          var hex = colors[k].replace('#', '');
          var r = parseInt(hex.substr(0, 2), 16) / 255;
          var g = parseInt(hex.substr(2, 2), 16) / 255;
          var b = parseInt(hex.substr(4, 2), 16) / 255;
          var lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
          if (lum < darkestLum) { darkestLum = lum; darkest = hex; }
        });
        if (darkest && darkestLum < 0.3) info.bgColor = darkest;
      }

      // Fallback: extract --bg-primary from CSS
      if (!info.bgColor) {
        var bgMatch = html.match(/--bg-primary:\s*([#\w]+)/);
        if (bgMatch) info.bgColor = bgMatch[1].replace('#', '');
      }
    } catch (e) {
      console.warn('Theme extraction failed:', e);
    }
    return info;
  },

  /**
   * Capture a single slide element as a base64 PNG using html2canvas.
   * The html2canvas library must be loaded in the PARENT window.
   */
  _captureSlide: async function(slideEl, iframeWindow) {
    // html2canvas is loaded in the parent window; we need to pass the element
    // html2canvas can work cross-frame if same-origin
    var canvas = await html2canvas(slideEl, {
      width: 1920,
      height: 1080,
      scale: 1,
      useCORS: true,
      allowTaint: true,
      backgroundColor: null,
      logging: false,
      windowWidth: 1920,
      windowHeight: 1080
    });
    return canvas.toDataURL('image/png');
  },

  /**
   * Export presentation as PPTX with slide screenshots.
   * Each slide is rendered in a hidden iframe with all animations completed,
   * captured as an image via html2canvas, and inserted into the PPTX.
   * @param {Object} options - { title: string }
   */
  exportPPTX: async function(options) {
    options = options || {};
    var title = options.title || document.title;
    var slug = this.getSlug();
    var blocks = options.blocks || this.getBlockFiles();
    if (!blocks.length) { alert('No block files found on this page.'); return; }

    this.showProgress('Preparing PPTX export...');

    try {
      // Load libraries in parallel
      this.updateProgress('Loading libraries...', 5);
      await Promise.all([this.loadPptxGen(), this.loadHtml2Canvas()]);

      var pres = new PptxGenJS();
      pres.layout = 'LAYOUT_WIDE'; // 13.33 x 7.5 inches (16:9)
      pres.author = 'Reactive Presentation';
      pres.title = title;

      var totalSlides = 0;
      var self = this;

      for (var i = 0; i < blocks.length; i++) {
        var blockFile = blocks[i];
        this.updateProgress('Loading ' + blockFile + '...', 10 + (i / blocks.length) * 30);

        // Load block HTML in hidden iframe for full rendering
        var result;
        try {
          result = await this._loadBlockInIframe(blockFile);
        } catch (e) {
          console.warn('Skipping block:', blockFile, e);
          continue;
        }

        var iframeDoc = result.doc;
        var iframe = result.iframe;

        // Complete all animations (fragments visible, canvas at final step)
        this._completeAllAnimations(iframeDoc);

        // Wait a moment for canvas redraws to finish
        await new Promise(function(r) { setTimeout(r, 300); });

        // Capture each slide
        var slides = iframeDoc.querySelectorAll('.slide');
        for (var j = 0; j < slides.length; j++) {
          var slideEl = slides[j];
          totalSlides++;
          var pctBase = 40 + ((totalSlides - 1) / Math.max(slides.length * blocks.length, 1)) * 45;
          self.updateProgress('Capturing slide ' + totalSlides + '...', pctBase);

          // Ensure slide is properly sized for capture
          slideEl.style.width = '1920px';
          slideEl.style.height = '1080px';
          slideEl.style.minHeight = '1080px';
          slideEl.style.overflow = 'hidden';

          var pptxSlide = pres.addSlide();
          var slideHeading = slideEl.querySelector('h1, h2');

          try {
            var dataUrl = await self._captureSlide(slideEl, iframe.contentWindow);

            pptxSlide.addImage({
              data: dataUrl,
              x: 0, y: 0,
              w: '100%', h: '100%'
            });

            // Add heading text as slide notes (for searchability)
            if (slideHeading) {
              pptxSlide.addNotes(slideHeading.textContent.trim());
            }
          } catch (captureErr) {
            console.warn('Capture failed for slide ' + totalSlides + ', using text fallback:', captureErr);
            // Fallback: text-based slide
            if (slideHeading) {
              pptxSlide.addText(slideHeading.textContent.trim(), {
                x: 0.5, y: 0.5, w: '90%', fontSize: 24, color: 'FFFFFF', bold: true
              });
            }
            pptxSlide.background = { color: '1a1d2e' };
          }
        }

        // Clean up iframe
        document.body.removeChild(iframe);
      }

      this.updateProgress('Generating PPTX (' + totalSlides + ' slides)...', 90);
      await pres.writeFile({ fileName: slug + '.pptx' });

      this.hideProgress();
    } catch (err) {
      this.hideProgress();
      // Clean up any remaining iframes
      document.querySelectorAll('iframe[style*="-9999px"]').forEach(function(f) { f.remove(); });
      alert('PPTX export failed: ' + err.message);
      console.error('PPTX export error:', err);
    }
  },

  /** Show progress overlay */
  showProgress: function(msg) {
    var overlay = document.getElementById('export-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'export-overlay';
      overlay.className = 'export-overlay';
      overlay.innerHTML =
        '<div class="export-progress-content">' +
        '<div class="export-progress-text"></div>' +
        '<div class="export-progress-track"><div class="export-progress-bar"></div></div>' +
        '</div>';
      document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
    overlay.querySelector('.export-progress-text').textContent = msg || '';
    overlay.querySelector('.export-progress-bar').style.width = '0%';
  },

  /** Update progress overlay text and bar */
  updateProgress: function(msg, pct) {
    var overlay = document.getElementById('export-overlay');
    if (!overlay) return;
    if (msg) overlay.querySelector('.export-progress-text').textContent = msg;
    if (pct !== undefined) overlay.querySelector('.export-progress-bar').style.width = pct + '%';
  },

  /** Hide progress overlay */
  hideProgress: function() {
    var overlay = document.getElementById('export-overlay');
    if (overlay) overlay.style.display = 'none';
  }
};
