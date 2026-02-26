/**
 * Export Utilities for Reactive Presentation
 * PDF export (via browser print) and ZIP download (via JSZip CDN).
 * Include in TOC index.html pages: <script src="../common/export-utils.js"></script>
 */
const ExportUtils = {
  JSZIP_CDN: 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',

  /** Escape HTML special characters to prevent XSS in generated markup */
  _escapeHTML: function(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
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

  /**
   * Export all slides as PDF via browser print dialog.
   * Fetches all block HTML files, extracts slides, opens a print-optimized view.
   * @param {Object} options - { title: string }
   */
  exportPDF: async function(options) {
    options = options || {};
    var title = options.title || document.title;
    var blocks = this.getBlockFiles();
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
      var printHTML = '<!DOCTYPE html>\n<html lang="ko">\n<head>\n' +
        '<meta charset="UTF-8">\n' +
        '<base href="' + this._escapeHTML(baseURL) + '">\n' +
        '<title>' + this._escapeHTML(title) + ' - PDF Export</title>\n' +
        '<link rel="stylesheet" href="../common/theme.css">\n' +
        '<link rel="stylesheet" href="../common/theme-override.css">\n' +
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
   * Includes block HTMLs, TOC page, common framework files, and pptx-theme assets.
   * @param {Object} options - { slug: string }
   */
  downloadZIP: async function(options) {
    options = options || {};
    var slug = options.slug || this.getSlug();
    var blocks = this.getBlockFiles();
    if (!blocks.length) { alert('No block files found on this page.'); return; }

    this.showProgress('Preparing ZIP download...');

    try {
      this.updateProgress('Loading JSZip library...', 5);
      await this.loadJSZip();

      var zip = new JSZip();
      var slugFolder = zip.folder(slug);
      var commonFolder = zip.folder('common');
      var fetched = 0;
      var totalFiles = blocks.length + this.COMMON_FILES.length + 1;

      // Fetch block HTML files
      for (var i = 0; i < blocks.length; i++) {
        var file = blocks[i];
        this.updateProgress('Fetching ' + file + '...', 10 + (fetched / totalFiles) * 65);
        var resp = await fetch(file);
        if (resp.ok) slugFolder.file(file, await resp.text());
        fetched++;
      }

      // Fetch TOC index.html (current page)
      this.updateProgress('Fetching index.html...', 10 + (fetched / totalFiles) * 65);
      var tocResp = await fetch('index.html');
      if (tocResp.ok) slugFolder.file('index.html', await tocResp.text());
      fetched++;

      // Fetch common framework files
      for (var j = 0; j < this.COMMON_FILES.length; j++) {
        var cFile = this.COMMON_FILES[j];
        this.updateProgress('Fetching common/' + cFile + '...', 10 + (fetched / totalFiles) * 65);
        try {
          var cResp = await fetch('../common/' + cFile);
          if (cResp.ok) commonFolder.file(cFile, await cResp.text());
        } catch (e) { /* skip missing optional files */ }
        fetched++;
      }

      // Try to fetch pptx-theme assets
      try {
        var manifestResp = await fetch('../common/pptx-theme/theme-manifest.json');
        if (manifestResp.ok) {
          var manifest = await manifestResp.json();
          var themeFolder = commonFolder.folder('pptx-theme');
          themeFolder.file('theme-manifest.json', JSON.stringify(manifest, null, 2));
          if (manifest.images && Array.isArray(manifest.images)) {
            for (var k = 0; k < manifest.images.length; k++) {
              try {
                var imgResp = await fetch('../common/pptx-theme/images/' + manifest.images[k]);
                if (imgResp.ok) themeFolder.folder('images').file(manifest.images[k], await imgResp.blob());
              } catch (e) { /* skip missing images */ }
            }
          }
        }
      } catch (e) { /* no pptx-theme directory, skip */ }

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
