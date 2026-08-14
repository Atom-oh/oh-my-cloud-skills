# Relay-Chain Gate (co-agent:harness)

> **Scope:** an **opt-in** review gate for `/co-agent:harness` (H2 plan gate, H4 final
> gate) — `harness.review_mode == "relay"`. The default is the **hybrid** gate
> (`references/hybrid-gate.md`: parallel find → chair triage → parallel verify); `parallel`
> selects the one-shot independent fan-out (`consensus-mode.md`). Relay replaces both with
> a **sequential chain**: peers review one at a time, each building on the prior peers'
> findings, and the host (chair) synthesizes one high-confidence verdict at the end. Pick
> relay when priming-driven depth matters more than wall-clock (each peer must finish
> before the next starts). **Only harness reads `review_mode`** — `/co-agent:consensus`
> and the review/decide/ADR modes keep the parallel gate.

## Why relay instead of parallel

- **Parallel** (consensus-mode.md) = N *independent* opinions, then vote-with-verification.
  Good for breadth and for a quorum. Each peer sees only the artifact, never the others.
- **Relay** = one *cumulative* pass. Peer *k* sees the artifact **plus every prior peer's
  findings** and is asked to confirm/refute each and add what was missed. The chain deepens
  instead of duplicating, so the panel converges on **one thoroughly-vetted result in a
  single pass** — the harness goal ("go the full distance to produce one high-confidence
  result in a single pass").
- Trade-off: relay is **sequential** (slower wall-clock, no `&`/`wait`) and later peers are
  primed by earlier ones (less independence). That priming is the point here — the chair
  still verifies every surviving finding against the actual code, so a wrong early claim is
  caught, not amplified.

## Ordering

Process the gate-eligible `(ai, model)` pairs from `co_agent_config.py pairs` **in order**.
`pairs` emits a **round-robin interleave in the fixed `panel_ais` order** (kiro-cli, the
counterpart peer, agy) — at each round index it appends whichever AI still has a model left
at that index, so the AI(s) with the **most** configured `models` are always the ones left
in the tail once the shorter queues run out. There is no separate relay-order key; `enabled`
only drops an AI from the chain entirely, it cannot move it within the fixed order.

The tail of the chain is therefore the **last link of the strictly longest `models`
list** (round-robin: when the shorter queues run out, only the longest queue keeps
appending). To put the **strongest reasoner last**, give it a `models` list **strictly
longer than** every other enabled AI's — matching lengths ties the tail to `panel_ais`
order, which the peer loses. Two working examples against the committed default (kiro 3
models, peer/agy 1 each; default tail = kiro's 3rd model):
- lightweight: `set kiro-cli models claude-opus-4.8` + `set <peer> models m1,m2` →
  4 links `[kiro, peer, agy, peer]`, tail = the peer's 2nd model;
- full-width: `set <peer> models m1,m2,m3,m4` → 8 links (kiro 3 + peer 4 + agy 1), tail = the peer's 4th model.
**Mind the per-round cap** (`max_calls / max_rounds`; relay is single-phase): the trim
cuts the END of the interleaved list — exactly the tail links you just arranged — so keep
total pairs ≤ the cap (default 24/2 = 12). The harness H0 `matrix` display names any
trimmed-out pairs (the fan-out `pairs` calls themselves are silent), so check the H0 matrix
to see whether your tail links survived. A single gate-eligible pair degenerates to one
review (still valid — see Quorum).

## Multi-model relay — multi-directional verification

Each chain link is an `(ai, model)` **pair**, not just an AI: with the committed `deep`
profile, every model in an AI's `models` list becomes its own link, so **one relay pass
verifies from as many directions as there are configured models**. Kiro's mainstay panel
alone contributes two cross-vendor lenses (opus / minimax-m2.5 via the Kiro router);
add Codex and Agy and a default relay is 4 links deep — each model confirming/refuting the
accumulated findings from its own family's bias.

All of this is **headless-safe** — every model override goes through the flags each CLI
actually accepts non-interactively (`co_agent_config.py flags <ai> --model <m>`, the same
contract as `/co-agent:configure`):

| AI | headless model flag | multi-model via |
|----|--------------------|-----------------|
| kiro-cli | `--model` | `set kiro-cli models m1,m2,m3` |
| claude (codex-host panel) | `--model` (+ `--effort`) | `set claude models …` |
| codex | `-m` (+ `-c model_reasoning_effort`) | `set codex models …` |
| agy | `--model` (spaced tokens OK, e.g. `Gemini 3.1 Pro (High)`) | `set agy models …` |

Caps still apply: `pairs` trims to `consensus.max_calls / max_rounds` round-robin across
AIs (extra same-provider models are trimmed before a whole provider is dropped), and the
context-size `fits` guard skips a pair whose window can't hold the accumulated chain —
note that the chain **grows** as it relays, so late links need the largest windows —
since tail position is an emergent property of `models`-list lengths (see Ordering; there
is no placement knob), this means **give big-window AIs the longest `models` lists**.
Sequential relay costs wall-clock
(sum of links, not max) — trim `models` lists rather than lowering `timeout` if a run is
too slow.

## The gate (one relay round)

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"` and `CFG="$SK/co_agent_config.py"`.

```bash
RUN=$(mktemp -d "${TMPDIR:-/tmp}/co-agent-relay.XXXXXX"); trap 'rm -rf "$RUN"' EXIT
HOST="${CO_AGENT_HOST:-claude}"
T=$(python3 "$CFG" timeout --host "$HOST" 2>/dev/null || echo 240)

# The artifact under review (plan doc for H2, cumulative diff for H4). Secret-scan it and
# obtain consent BEFORE the first peer — same data boundary as the parallel fan-out.
ARTIFACT="$RUN/artifact.txt"      # write the plan / cumulative diff here first
CHAIN="$RUN/chain.md"; : > "$CHAIN"   # accumulated prior findings (empty for peer #1)

# Fixed per-peer instruction — NEVER built from repo content.
BASE_PROMPT='You are one reviewer in a RELAY CHAIN. Review the ARTIFACT below for
correctness, scope, completeness, and AWS security mandate violations (no 0.0.0.0/0, no
IAM Principal "*", no secrets in env). If PRIOR FINDINGS are present, first CONFIRM or
REFUTE each against the actual content (cite the line/section), then ADD anything missed.
Do not repeat a prior finding you agree with — just mark it CONFIRMED. Output a single
consolidated findings list; label each CRITICAL / MAJOR / MINOR / NIT with evidence.'

i=0
while IFS=$'\t' read -r ai model; do
  i=$((i+1)); slot="$RUN/${i}-${ai}"
  # Per-peer context = the artifact + everything the chain has accumulated so far.
  CTX="$RUN/${i}-ctx.txt"
  { echo "=== ARTIFACT ==="; cat "$ARTIFACT"; echo;
    if [ -s "$CHAIN" ]; then echo "=== PRIOR FINDINGS (relay so far) ==="; cat "$CHAIN"; fi
  } > "$CTX"
  mapfile -t MFLAGS < <(python3 "$CFG" flags "$ai" --model "$model" --host "$HOST" 2>/dev/null || true)
  TOK=$(( ( $(wc -c < "$CTX") + 3 ) / 4 ))
  if ! python3 "$CFG" fits "$ai" "$TOK" --host "$HOST" 2>/dev/null; then
    echo "[skip] $ai/$model — ctx ~${TOK} tok > window"; continue
  fi
  # SEQUENTIAL — no `&`, no `wait`. Each peer must finish before the next starts so its
  # findings enter the chain. Same adapters as ai-cli-adapters.md (stdin for codex/claude/
  # agy; kiro reads the ctx file via fs_read since it ignores stdin).
  case "$ai" in
    # kiro-cli reads its input from argv, not stdin — but it still INHERITS this loop's
    # stdin (the `pairs` process substitution) unless explicitly redirected. If kiro-cli
    # reads/drains stdin at all while running, the next `read -r ai model` sees EOF and the
    # chain silently truncates after this link — `< /dev/null` closes that channel.
    kiro-cli) command -v kiro-cli >/dev/null 2>&1 && timeout "$T" \
                kiro-cli chat "$BASE_PROMPT"$'\n\n'"Read the review context with fs_read from: $CTX" \
                "${MFLAGS[@]}" --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never \
                < /dev/null > "$slot.md" 2>"$slot.err" || echo "[skip] kiro-cli/$model" ;;
    claude)   command -v claude >/dev/null 2>&1 && cat "$CTX" | timeout "$T" \
                claude -p "$BASE_PROMPT" "${MFLAGS[@]}" --permission-mode plan \
                --tools Read,Grep,Glob --output-format text > "$slot.md" 2>"$slot.err" || echo "[skip] claude/$model" ;;
    codex)    command -v codex >/dev/null 2>&1 && cat "$CTX" | timeout "$T" \
                codex exec -s read-only "${MFLAGS[@]}" "$BASE_PROMPT" > "$slot.md" 2>"$slot.err" || echo "[skip] codex/$model" ;;
    agy)      command -v agy >/dev/null 2>&1 && cat "$CTX" | timeout "$T" \
                agy -p "$BASE_PROMPT" "${MFLAGS[@]}" --sandbox > "$slot.md" 2>"$slot.err" || echo "[skip] agy/$model" ;;
  esac
  # Fold this peer's output into the chain for the NEXT peer. Skip empty/errored output.
  if [ -s "$slot.md" ]; then
    { echo; echo "## Reviewer $i — $ai/$model"; cat "$slot.md"; } >> "$CHAIN"
  fi
done < <(python3 "$CFG" pairs --host "$HOST")   # pairs is silent; the trim/budget warning is shown by the H0 `matrix` call above
# The final $CHAIN holds the full relay. The host (chair) synthesizes from it — see below.
```

## Chair synthesis (host) — unchanged verification, cumulative input

The chain is **advisory input**, not the verdict. The host:

1. Runs `check_citations.py` over the accumulated findings → drop `unsupported`, flag
   `needs-review`. A finding a later peer marked CONFIRMED still needs a real citation.
2. Verifies each surviving finding **against the actual plan/diff** — a relay can propagate
   an early peer's mistake down the chain, so confirm, don't trust the "CONFIRMED" label.
3. Attributes dissent: "Reviewer 2 refuted Reviewer 1's X" is signal, keep it in the report.
4. Emits the verdict (PASS / REVIEW / FAIL) and, on CRITICAL/MAJOR, the fix list.

## Quorum (relay differs from parallel)

Relay is **cumulative**, not independent votes, so parallel's "≤1 usable pair → single-
opinion, not consensus" rule does **not** apply — one relayed pass with **≥1 peer** that
produced output is a valid gate result (the chair still verifies every finding). But harness
is **non-degraded**: if **zero** gate-eligible peers produced any output, do **not** solo —
`consensus_state.py set . status needs-human` (H2) / block and tell the user to run
`/co-agent:setup`, exactly as the parallel gate does.

## Loop-until-done

Same as the parallel gate: repeat the relay round up to `consensus.max_rounds` (default 2)
until no CRITICAL/MAJOR finding survives the chair's verification (also stop on no-progress /
oscillation). Between rounds, reset `$CHAIN` and re-run the chain on the *updated* artifact —
each round is a fresh relay over the current plan/diff, not an append to the prior round.
Record the outcome via `consensus_state.py stage-result` (`…/plan-gate/result.json` for H2,
`…/code-gate/result.json` for H4), then advance the harness phase.

## Security

Identical trust boundary to `ai-cli-adapters.md` — the artifact is secret-scanned and
consented before the first peer; context goes via stdin (kiro via a temp file + `fs_read`);
peers run read-only/sandboxed with a sanitized env. The **added** exposure is that each
peer's context now includes prior peers' text (`$CHAIN`), which is peer-generated, not repo
content — so it carries no new secret, but a compromised peer could try prompt-injection on
the next. Mitigation is the same: the chair treats all peer output as advisory and verifies
against the code; no peer's verdict is authoritative.
