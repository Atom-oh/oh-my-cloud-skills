#!/bin/bash
# validator (new omcs chair_valid) vs gate (pr-review.yml) agreement check
chair_valid() {
  [ -s "$OUT" ] || return 1
  local last verdict_count
  last="$(awk 'NF{last=$0} END{print last}' "$OUT")"
  verdict_count="$(grep -c '^VERDICT:' "$OUT" || true)"
  [[ "$last" =~ ^VERDICT:\ (PASS|FAIL)$ ]] && [ "$verdict_count" = "1" ]
}
gate_pass() {  # mirrors the workflow gate: FAIL wins, then PASS, else fail-closed
  grep -q "^VERDICT: FAIL$" "$OUT" && { echo fail; return; }
  grep -q "^VERDICT: PASS$" "$OUT" && { echo pass; return; }
  echo "no-verdict"
}
old_degraded() { [ ! -s "$OUT" ] || ! grep -q '^VERDICT:' "$OUT"; }

t(){ desc="$1"; body="$2"; OUT=$(mktemp); printf '%s' "$body" > "$OUT"
  chair_valid && v=valid || v=INVALID
  old_degraded && o=degraded || o=ok
  printf "%-42s new=%-8s old=%-9s gate=%s\n" "$desc" "$v" "$o" "$(gate_pass)"; rm -f "$OUT"; }

t "clean FAIL"                 $'review body\n\nVERDICT: FAIL\n'
t "clean PASS"                 $'review body\n\nVERDICT: PASS\n'
t "verdict + trailing text"    $'body\n\nVERDICT: FAIL (3 MAJOR)\n'
t "duplicate verdict quoted"   $'body quoting VERDICT: PASS\n\nVERDICT: FAIL\n'
t "verdict not last"           $'VERDICT: FAIL\n\nmore text after\n'
t "empty output"               ''
t "Execution error only"       $'Execution error\n'
