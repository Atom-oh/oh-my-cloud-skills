# Verification

Show nothing before these pass.

1. `remarp_to_slides.py validate` has no CRITICAL finding and no `RAW_HEX` or `EM_DASH` from the
   slide, and `check_deck.py` on the built deck reports no `NOTE_OPERATING_INSTRUCTION` or
   `NOTE_MARK_IN_META` for it.
2. Build, serve over http, open the slide. Console has no errors (a missing `favicon.ico` is
   not one).
3. Step through every phase in light and dark. At each step: the right parts are lit, the packet
   is on the right wire, the callout badge matches, nothing is clipped, the side panel fits
   (progress bar visible at the bottom).
4. `deck.getStepInfo()` reports `cur` from 0 to the number of phases and `more: false` on the
   last step. The number of `↓` marks in the notes equals the number of phases.
5. Reduced motion: with the preference on, each Down shows the step's end state at once and
   nothing moves afterwards: figures stand at their end position and a `busy` figure shows no
   nod, sweat drop or glyphs.
6. Leave the slide and come back: the side panel and camera are on step 0 already during the slide transition (the first 350 ms), and figures stand at their start position.
7. PDF export: the scene slide shows the host's static fallback (the sentence and the numbered
   steps), not a blank body. The print view runs no slide scripts, so this is the expected PDF
   content.

A stepping script, using Python Playwright and a local chromium:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.goto('http://127.0.0.1:8000/default.html#2'); pg.wait_for_timeout(1500)
    for i in range(PHASES + 1):
        if i: pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(2600)
        print(i, pg.evaluate('JSON.stringify(deck.getStepInfo())'))
        pg.screenshot(path=f'step-{i}.png')
```

Look at the screenshots. A passing script does not mean the picture is right.
