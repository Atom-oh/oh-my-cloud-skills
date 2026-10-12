/**
 * Rendered reveal regressions. Run separately from dependency-free TAP suites:
 * REACTIVE_REVEAL_PLAYWRIGHT_MODULE=/path/to/playwright \
 * REACTIVE_REVEAL_CHROMIUM=/path/to/chrome \
 * node tests/structure/test-reactive-reveal-browser.js [--report /tmp/report.json]
 * Use --interactions-only for the supplemental quiz/chrome/nowrap cases.
 *
 * Uses disposable pages, local repository assets and no network requests.
 */
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.REACTIVE_REVEAL_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../..');
const assets = path.join(root, 'plugins/aws-content-plugin/skills/reactive-presentation/assets');
const read = name => fs.readFileSync(path.join(assets, name), 'utf8');
const css = read('design-tokens.css') + '\n' + read('theme.css').replace(/^@import.*;\s*$/mg, '');
const framework = read('slide-framework.js');
const exporter = read('export-utils.js');
const quizzes = read('quiz-component.js');
const cards = count => Array.from({length: count}, (_, index) =>
  `<div class="card"><strong>Card ${index + 1}</strong><p class="card-desc">One clear point.</p></div>`).join('');
const reportIndex = process.argv.indexOf('--report');
const reportPath = reportIndex < 0 ? null : process.argv[reportIndex + 1];
const interactionsOnly = process.argv.includes('--interactions-only');
if (reportIndex >= 0 && !reportPath) throw new Error('--report requires a path');

async function fixture(browser, markup, options = {}) {
  const page = await browser.newPage({
    viewport: options.viewport || {width: 1920, height: 1080},
    reducedMotion: options.reducedMotion || 'no-preference',
  });
  await page.route('**/*', route => route.abort());
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.setContent(`<!doctype html><html lang="en"><head><style>${css}</style></head><body>
    <div class="slide-deck ${options.theme === 'dark' ? 'theme-dark' : ''}">
      ${options.slideMarkup || `<div class="slide"><div class="slide-header"><h2>Reveal regression</h2></div>
        <div class="slide-body">${markup}</div></div>`}
    </div></body></html>`);
  await page.addScriptTag({content: framework});
  await page.addScriptTag({content: exporter});
  if (options.quiz) await page.addScriptTag({content: quizzes});
  await page.evaluate(options => {
    window.exporter = ExportUtils;
    window.framework = new SlideFramework({sidebar: false, footer: options.footer || null});
    document.dispatchEvent(new Event('DOMContentLoaded'));
  }, {footer: options.footer});
  return {page, errors};
}

async function state(page) {
  return page.evaluate(() => {
    const slide = document.querySelector('.slide');
    const box = slide.querySelector('.fit-box');
    const grid = slide.querySelector('.card-grid');
    const deck = document.querySelector('.slide-deck').getBoundingClientRect();
    return {
      fit: Number(slide.dataset.fitScale),
      overflow: slide.hasAttribute('data-fit-overflow'),
      columns: grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').length : null,
      box: box ? {width: box.clientWidth, scroll: box.scrollWidth} : null,
      deck: {left: deck.left, top: deck.top, right: deck.right, bottom: deck.bottom},
      cards: [...slide.querySelectorAll('.card')].map(element => {
        const style = getComputedStyle(element);
        return {opacity: Number(style.opacity), transform: style.transform,
          width: element.clientWidth, scroll: element.scrollWidth};
      }),
    };
  });
}

function assertFits(result, label) {
  assert.equal(result.overflow, false, `${label}: transient motion must not mark overflow`);
  assert.ok(result.fit >= 0.82 && result.fit <= 1.35, `${label}: fit scale within supported bounds`);
  assert.ok(result.box.scroll <= result.box.width + 1, `${label}: no box overflow`);
  for (const card of result.cards) {
    assert.ok(card.scroll <= card.width + 1, `${label}: no text spill inside a card`);
  }
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.REACTIVE_REVEAL_CHROMIUM ?
      {executablePath: process.env.REACTIVE_REVEAL_CHROMIUM} : {}),
  });
  const report = {browser: browser.version(), network: 'all requests blocked', cases: []};
  try {
    // Startup and later forced refits: content is sparse enough for MAX, even while
    // positive-X keyframe transforms are running. Refits preserve animation objects.
    for (const viewport of interactionsOnly ? [] : [{width: 1920, height: 1080},
      {width: 1280, height: 720}, {width: 3840, height: 2160}]) {
      for (const theme of ['light', 'dark']) {
        for (const count of [3, 5, 7, 9]) {
          const label = `${viewport.width}x${viewport.height}/${theme}/${count} cards`;
          const {page, errors} = await fixture(browser,
            `<div class="card-grid" data-reveal="stagger" data-reveal-anim="left">${cards(count)}</div>`,
            {viewport, theme, footer: 'Local test footer'});
          try {
            const initial = await state(page);
            assert.equal(initial.fit, 1.35, `${label}: startup measures the final geometry`);
            assert.equal(initial.overflow, false, `${label}: no cached transient overflow`);
            if (count >= 5) assert.equal(initial.columns, count === 7 ? 4 : 3);
            assert.ok(initial.deck.left >= -1 && initial.deck.top >= -1);
            assert.ok(initial.deck.right <= viewport.width + 1 &&
              initial.deck.bottom <= viewport.height + 1);
            await page.waitForTimeout(180);
            const timeline = await page.evaluate(() => {
              const elements = [...document.querySelectorAll('.card')];
              const before = elements.map(element => element.getAnimations()[0]);
              const times = before.map(animation => animation && animation.currentTime);
              window.ReactiveFit.fitSlide(document.querySelector('.slide'),
                {force: true, shrinkOnly: true});
              const after = elements.map(element => element.getAnimations()[0]);
              return {
                retained: before.every((animation, index) => animation && animation === after[index]),
                forward: after.every((animation, index) =>
                  animation && animation.currentTime >= times[index] - 1),
              };
            });
            assert.deepEqual(timeline, {retained: true, forward: true},
              `${label}: fitting must not cancel or restart live keyframes`);
            // Do not use transformed live geometry for this final layout assertion.
            await page.waitForTimeout(1250);
            const settled = await state(page);
            assertFits(settled, label);
            assert.equal(settled.fit, 1.35);
            assert.deepEqual(errors, []);
            report.cases.push({name: 'startup-and-refit', label, initial, settled, timeline});
          } finally {
            await page.close();
          }
        }
      }
    }

    // Browser PPTX export must complete every delayed child immediately rather than
    // relying on the existing 300ms canvas-settle wait or a particular card count.
    for (const theme of interactionsOnly ? [] : ['light', 'dark']) {
      for (const count of [5, 7, 9]) {
        const {page, errors} = await fixture(browser,
          `<div class="card-grid fragment" data-fragment-index="1" data-reveal="stagger"
             data-reveal-pace="slow">${cards(count)}</div>`, {theme});
        try {
          await page.evaluate(() => window.exporter._completeAllAnimations(document));
          const immediate = await state(page);
          assert.ok(immediate.cards.every(card => card.opacity === 1 && card.transform === 'none'),
            `${theme}/${count}: export must not capture an unrevealed card`);
          assertFits(immediate, `${theme}/${count} exported cards`);
          await page.waitForTimeout(300);
          const capture = await state(page);
          assert.ok(capture.cards.every(card => card.opacity === 1 && card.transform === 'none'));
          const idempotent = await page.evaluate(() => {
            window.exporter._completeAllAnimations(document);
            return document.querySelectorAll('#reactive-export-final-state').length;
          });
          assert.equal(idempotent, 1);
          assert.deepEqual(errors, []);
          report.cases.push({name: 'browser-export', theme, count, immediate, capture});
        } finally {
          await page.close();
        }
      }
    }

    const {page, errors} = await fixture(browser,
      `<div class="card-grid fragment" data-fragment-index="1" data-reveal="stagger"
         data-reveal-pace="slow">${cards(9)}</div>`, {reducedMotion: 'reduce'});
    try {
      await page.evaluate(() => window.framework.revealNextFragment());
      const motion = await page.evaluate(() => [...document.querySelectorAll('.card')].map(element => {
        const style = getComputedStyle(element);
        return {delay: style.transitionDelay, transform: style.transform, animation: style.animationName};
      }));
      assert.ok(motion.every(card => card.delay === '0s' &&
        card.transform === 'none' && card.animation === 'none'));
      await page.waitForTimeout(500);
      const shown = await state(page);
      assert.ok(shown.cards.every(card => card.opacity === 1));
      assertFits(shown, 'reduced motion');
      assert.deepEqual(errors, []);
      report.cases.push({name: 'reduced-motion', motion, shown});
    } finally {
      await page.close();
    }

    // A deliberate per-deck column override must win over balanced-grid defaults.
    const custom = await fixture(browser,
      `<div class="card-grid" data-reveal="static"
         style="grid-template-columns:repeat(2,minmax(0,1fr))">${cards(7)}</div>`);
    try {
      const result = await state(custom.page);
      assert.equal(result.columns, 2);
      assertFits(result, 'custom grid override');
      report.cases.push({name: 'custom-grid', result});
    } finally {
      await custom.page.close();
    }

    // Font-role changes must preserve feedback fitting and the wrong-answer retry.
    for (const theme of ['light', 'dark']) {
      const quiz = await fixture(browser, `<div class="quiz" data-quiz="regression"
          data-explain="A brief explanation that remains visible after fitting.">
        <div class="quiz-question">Which choice is correct?</div>
        <div class="quiz-options"><button class="quiz-option" data-correct="false">Try again</button>
          <button class="quiz-option" data-correct="true">Correct choice</button></div>
        <div class="quiz-feedback"></div></div>`,
      {theme, quiz: true, viewport: {width: 1280, height: 720}});
      try {
        const initial = await state(quiz.page);
        await quiz.page.locator('.quiz-option[data-correct="false"]').click();
        const wrong = await state(quiz.page);
        assertFits(wrong, `${theme} wrong quiz answer`);
        assert.ok(wrong.fit <= initial.fit);
        await quiz.page.waitForTimeout(1800);
        assert.equal(await quiz.page.locator('.quiz-feedback').evaluate(element =>
          element.classList.contains('show')), false);
        const retry = await state(quiz.page);
        assert.equal(retry.fit, initial.fit);
        await quiz.page.locator('.quiz-option[data-correct="true"]').click();
        await quiz.page.waitForTimeout(350);
        const correct = await state(quiz.page);
        assertFits(correct, `${theme} correct quiz answer`);
        const feedback = await quiz.page.locator('.quiz-feedback').evaluate(element => ({
          visible: element.classList.contains('show'),
          clipped: element.scrollHeight > element.clientHeight + 1,
          text: element.textContent,
          questionFont: parseFloat(getComputedStyle(document.querySelector('.quiz-question')).fontSize),
          optionFont: parseFloat(getComputedStyle(document.querySelector('.quiz-option')).fontSize),
        }));
        assert.equal(feedback.visible, true);
        assert.equal(feedback.clipped, false);
        assert.match(feedback.text, /A brief explanation/);
        assert.ok(Math.abs(feedback.questionFont - 32) < 0.1);
        assert.ok(Math.abs(feedback.optionFont - 28) < 0.1);
        assert.deepEqual(quiz.errors, []);
        report.cases.push({name: 'quiz-feedback-and-retry', theme, initial, wrong, retry, correct, feedback});
      } finally {
        await quiz.page.close();
      }
    }

    // The added inner-card check detects a nowrap token that fits the full body
    // but spills from one fixed-width track at MAX scale.
    const nowrap = await fixture(browser,
      `<div class="card-grid" style="grid-template-columns:repeat(2,minmax(0,1fr))">
        <div class="card"><code>${'M'.repeat(48)}</code></div><div class="card">Neighbour</div></div>`);
    try {
      const result = await state(nowrap.page);
      assertFits(result, 'nowrap card token');
      assert.ok(result.fit < 1.35, 'inner-card overflow must constrain the fitted scale');
      report.cases.push({name: 'nowrap-card-token', result});
    } finally {
      await nowrap.page.close();
    }

    // Chrome reserves its band while present, and an explicit full-bleed cover
    // keeps zero padding and hides the footer.
    const chrome = await fixture(browser, cards(1), {footer: 'Footer band'});
    try {
      const band = await chrome.page.evaluate(() => ({
        padding: parseFloat(getComputedStyle(document.querySelector('.slide')).paddingBottom),
        footer: getComputedStyle(document.querySelector('.slide-footer')).display,
      }));
      assert.equal(band.padding, 96);
      assert.notEqual(band.footer, 'none');
      report.cases.push({name: 'footer-band', band});
    } finally {
      await chrome.page.close();
    }
    const coverSource = [
      'import sys',
      'sys.dont_write_bytecode = True',
      `sys.path.insert(0, ${JSON.stringify(path.join(root,
        'plugins/aws-content-plugin/skills/reactive-presentation/scripts'))})`,
      'import remarp_to_slides as r',
      '_, blocks = r.RemarpParser("---\\nremarp: true\\n---\\n@type: cover\\n# Local cover\\n\\n## Subtitle\\n").parse()',
      'slide = next(s for group in blocks.values() for s in group)',
      'print(r.RemarpHTMLGenerator().slide_to_html(slide))',
    ].join('\n');
    const coverMarkup = execFileSync('python3', ['-B', '-c', coverSource], {encoding: 'utf8'});
    const cover = await fixture(browser, '', {
      slideMarkup: coverMarkup.replace('<div class="slide', '<div data-hide-chrome class="slide'),
      footer: 'Hidden on the cover',
    });
    try {
      const geometry = await cover.page.evaluate(() => {
        const slide = document.querySelector('.slide');
        const glow = slide.querySelector('div');
        const frame = slide.getBoundingClientRect();
        const rect = glow.getBoundingClientRect();
        return {padding: getComputedStyle(slide).paddingBottom,
          footer: getComputedStyle(document.querySelector('.slide-footer')).display,
          frame: {left: frame.left, top: frame.top, right: frame.right, bottom: frame.bottom},
          glow: {left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom}};
      });
      assert.equal(geometry.padding, '0px');
      assert.equal(geometry.footer, 'none');
      assert.ok(geometry.glow.left >= geometry.frame.left - 1 &&
        geometry.glow.top >= geometry.frame.top - 1 &&
        geometry.glow.right <= geometry.frame.right + 1 &&
        geometry.glow.bottom <= geometry.frame.bottom + 1, 'cover glow remains inside the slide');
      assert.deepEqual(cover.errors, []);
      report.cases.push({name: 'cover-glow-and-hidden-chrome', geometry});
    } finally {
      await cover.page.close();
    }
    if (reportPath) fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
    console.log(`PASS ${report.cases.length} local rendered reveal cases on Chromium ${report.browser}`);
  } finally {
    await browser.close();
  }
}

main().catch(error => {console.error(error.stack); process.exitCode = 1;});
