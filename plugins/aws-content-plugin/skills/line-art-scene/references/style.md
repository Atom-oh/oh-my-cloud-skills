# Style

One thin pen on paper. The scene must read as a drawing, not a UI.

- **Pen**: 1.5 units, round caps and joins, ink is `currentColor`. A shared wobble filter
  (`inkDefs`) gives hand-drawn shake to parts and figures; text and callouts stay clean.
- **Paper**: `--surface-1`. Faces use `--surface-2` (front), `--surface-3` (top) and the paper
  (side) so a box reads as solid without gradients.
- **Accent**: exactly one accent for the active thing (`--accent`), `--info` for the alternative
  path, `--danger` for the blocked path, `--success` for passed checks. No other colours.
- **Proportions**: figures are about 95 units tall in their own space, feet on y = 120, facing +x.
  Limbs are two open strokes around a paper band, stopping short at the far end. Joints are
  rounded, edges bow slightly, nothing is ruler straight.
- **Clothes** are drawn around the skeleton, not on top of it. Sleeves and bags swing on springs.
- **Callouts** are short: a title of about 20 characters and an optional sub line.
- **Density**: at most about 8 parts and 6 callouts. More means split the story across slides.
- **Avoid**: gradients, glows other than the packet, drop shadows, decorative gradient orbs,
  rigid clothes that ignore the legs, a whole set of components that all look alike.
- **New means new**: when asked for "like this but new", keep the medium, pen and timing feel and
  invent the characters, props and activities.
