#!/usr/bin/env python3
"""
check_brochure.py — fast structural / responsive / accessibility gate for a brochure HTML.

Not a substitute for looking at the rendered page, but it catches the mistakes that
silently ship: unbalanced tags, missing responsive primitives, missing a11y primitives,
broken local asset references, and low-contrast muted text on a light background.

Usage:
    python3 check_brochure.py <brochure.html>

Exit code 0 = all good, 1 = one or more checks failed.
"""
import os
import re
import sys

def main():
    # --mobile-breakpoint N: the max-width the mobile media query must use.
    # Brochures use 640 (this skill's design system); the profile-page skill
    # reuses this checker with 768 (its design spec stacks the sidebar there).
    args = sys.argv[1:]
    bp = "640"
    if "--mobile-breakpoint" in args:
        i = args.index("--mobile-breakpoint")
        if i + 1 >= len(args) or not args[i + 1].isdigit():
            print("usage: check_brochure.py <brochure.html> [--mobile-breakpoint N]"); return 2
        bp = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        print("usage: check_brochure.py <brochure.html> [--mobile-breakpoint N]"); return 2
    path = args[0]
    if not os.path.isfile(path):
        print(f"FAIL  file not found: {path}"); return 1
    with open(path, encoding="utf-8") as f:
        html = f.read()
    base = os.path.dirname(os.path.abspath(path))
    fails, warns, oks = [], [], []

    def need(cond, label, hard=True):
        (oks if cond else (fails if hard else warns)).append(label)

    # --- tag balance (container tags) ---
    for t in ("section", "figure", "footer", "style", "script", "table", "head", "body"):
        o = len(re.findall(rf"<{t}[\s>]", html, re.I))
        c = len(re.findall(rf"</{t}>", html, re.I))
        need(o == c, f"tag balance <{t}> ({o} open / {c} close)")

    # --- responsive primitives ---
    need('name="viewport"' in html and "width=device-width" in html, "viewport meta (responsive)")
    need(bool(re.search(rf"@media[^{{]*max-width\s*:\s*{bp}", html)), f"mobile breakpoint (<={bp}px)")
    need(bool(re.search(r"@media[^{]*max-width\s*:\s*1024", html)), "tablet breakpoint (<=1024px)", hard=False)

    # --- accessibility primitives ---
    need(":focus-visible" in html, "keyboard :focus-visible styles")
    need("skip-link" in html or re.search(r'href="#(main|content|main-content|value)"', html) is not None,
         "skip link to main content", hard=False)
    need("prefers-reduced-motion" in html, "prefers-reduced-motion handling")
    if re.search(r"<animate[\s>]", html):
        need("svg animate" in html or "querySelectorAll('svg animate" in html or 'querySelectorAll("svg animate' in html,
             "SVG SMIL <animate> disabled under reduced-motion (CSS can't do it)", hard=False)

    # --- local asset references resolve ---
    for ref in re.findall(r'(?:src|href)="([^":#?]+\.(?:svg|png|jpg|jpeg|webp|drawio|css|js))"', html):
        if ref.startswith("http") or ref.startswith("//") or ref.startswith("data:"):
            continue
        need(os.path.isfile(os.path.join(base, ref)), f"local asset exists: {ref}")

    # --- contrast smell test: muted text token must not be the too-light ink-400 ---
    if re.search(r"--text-3\s*:\s*var\(--ink-400\)", html) or re.search(r"--text-3\s*:\s*#8[aA]8474", html):
        warns.append("muted text token (--text-3) is ~3.2:1 on paper — fails WCAG AA; darken to ~#6B665A")

    # --- self-contained-ish: CSS is inlined ---
    need("<style" in html, "inlined <style> (self-contained)", hard=False)

    # --- report ---
    for o in oks:   print(f"  ok    {o}")
    for w in warns: print(f"  WARN  {w}")
    for f in fails: print(f"  FAIL  {f}")
    print(f"\n{len(oks)} ok · {len(warns)} warn · {len(fails)} fail")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
