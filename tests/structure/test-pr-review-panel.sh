#!/bin/bash
# Exercise Kiro model selection, no-tools, preflight, fallback and quota behavior with local stubs.
# Review-cell retry and transport coverage also lives in tests/pr-review/test-run-panel.sh.
# The historical CLI assumptions are documented in docs/runbooks/pr-review-panel.md.
PANEL="scripts/pr-review/run-panel.sh"
SYNTH="scripts/pr-review/synthesize.sh"
AGENT="scripts/pr-review/agents/pr-review-notools.json"

assert_bash_syntax "$PANEL" "run-panel.sh valid bash"
assert_bash_syntax "$SYNTH" "synthesize.sh valid bash"
assert_file_exists "$AGENT" "kiro no-tools agent config present"
assert_json_valid "$AGENT" "kiro no-tools agent config is valid JSON"

AGENT_NAME=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$AGENT" 2>/dev/null || true)
assert_eq "pr-review-notools" "$AGENT_NAME" "agent .name is pr-review-notools"

AGENT_TOOLS=$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(len(d.get("tools",["x"])), len(d.get("mcpServers",{"x":1})))' "$AGENT" 2>/dev/null || true)
assert_eq "0 0" "$AGENT_TOOLS" "agent declares tools: [] and no mcpServers"

PANEL_SRC=$(grep -v '^\s*#' "$PANEL")
assert_grep_match 'kiro-cli chat .*--agent "\$KIRO_AGENT_NAME"' "$(echo "$PANEL_SRC" | tr '\n' ' ')" \
    "run-panel.sh passes --agent \"\$KIRO_AGENT_NAME\" to kiro-cli chat"
assert_grep_match 'cp "\$KIRO_AGENT_SRC" "\$CELL_CWD/\.kiro/agents/"' "$PANEL_SRC" \
    "run-panel.sh copies the agent file into each cell cwd"
assert_grep_no_match '\-{2}trust-tools' "$PANEL_SRC" \
    "run-panel.sh no longer relies on --trust-tools= (ignored by kiro-cli 2.11.1)"
assert_grep_no_match '\-{2}mode default' "$PANEL_SRC" \
    "run-panel.sh no longer passes the v3-only --mode default flag"
assert_grep_no_match '-{2}v3\b|-{2}agent-engine(?:[ \t]+|=)(?!v1(?:[ \t]|$))' "$PANEL_SRC" \
    "run-panel.sh permits only agent-engine v1; v2 and v3 are forbidden"

assert_grep_match 'Monthly request limit reached' "$PANEL_SRC" \
    "run-panel.sh detects the Kiro monthly quota signature (v2 stderr)"
assert_grep_match 'MONTHLY_REQUEST_COUNT' "$PANEL_SRC" \
    "run-panel.sh detects the Kiro monthly quota signature (v3/JSON)"
assert_grep_match 'kiro-quota\.flag' "$PANEL_SRC" \
    "run-panel.sh writes kiro-quota.flag for synthesize.sh"
assert_grep_match 'kiro-quota\.flag' "$(grep -v '^\s*#' "$SYNTH")" \
    "synthesize.sh renders the Kiro quota banner"
assert_grep_match 'no agent with name' "$PANEL_SRC" \
    "run-panel.sh detects the --agent fallback signature"
assert_grep_match 'kiro-agent-fallback\.flag' "$(grep -v '^\s*#' "$SYNTH")" \
    "synthesize.sh renders the agent-fallback banner"
assert_grep_match 'kiro-preflight\.flag' "$(grep -v '^\s*#' "$SYNTH")" \
    "synthesize.sh renders the preflight-failure banner"
assert_file_exists "docs/runbooks/pr-review-panel.md" "runbook for the panel failure modes exists"

# A monthly-limit response with exit 0 and empty stdout must stop retries and retain diagnostics.
if command -v timeout >/dev/null 2>&1; then
    T_STUB=$(mktemp -d)
    # Review stubs answer the version and fixed canary requests before exercising review-cell behavior.
    wrap_kiro_stub() {
        {
            cat <<'PREFLIGHT_STUB'
#!/bin/bash
if [ "${1:-}" = "--version" ]; then
    echo "kiro-cli test"
    exit 0
fi
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    echo "NO_TOOLS"
    exit 0
fi
PREFLIGHT_STUB
            cat "$T_STUB/kiro-cli"
        } > "$T_STUB/kiro-cli.wrapped"
        mv "$T_STUB/kiro-cli.wrapped" "$T_STUB/kiro-cli"
        chmod +x "$T_STUB/kiro-cli"
    }
    cat > "$T_STUB/kiro-cli" <<'EOF'
#!/bin/bash
printf 'Monthly request limit reached\nThe limits reset on 10/01.\n' >&2
exit 0
EOF
    cat > "$T_STUB/codex" <<'EOF'
#!/bin/bash
cat > /dev/null; echo "no findings"
EOF
    chmod +x "$T_STUB/kiro-cli" "$T_STUB/codex"
    wrap_kiro_stub
    mkdir -p "$T_STUB/lenses" && echo "lens" > "$T_STUB/lenses/L2.txt"
    printf 'diff --git a/x b/x\n+x\n' > "$T_STUB/diff.txt"
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    assert_grep_match '^run-panel\.sh: kiro-cli test' "$PANEL_OUT" "kiro-cli --version is logged as the first line"
    assert_grep_no_match '\[retry ' "$PANEL_OUT" "quota exhaustion is not retried"
    assert_grep_match '\[quota\] kiro-opus-L2' "$PANEL_OUT" "quota exhaustion is logged per cell"
    assert_grep_match '::error::Kiro request quota exhausted.*reset on 10/01' "$PANEL_OUT" \
        "quota exhaustion is reported as ::error:: with the reset date"
    assert_file_exists "$T_STUB/work/kiro-quota.flag" "quota exhaustion leaves kiro-quota.flag"
    assert_file_exists "$T_STUB/work/coverage-severe.flag" "quota exhaustion still forces coverage-severe (fail-closed kept)"

    # The JSON/error-output variant must still be recognized from stderr only.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
echo "You've reached your monthly usage limit."
echo '[ERROR] [KRS] HTTP 400 body={"__type":"...ServiceQuotaExceededException","reason":"MONTHLY_REQUEST_COUNT"}' >&2
exit 1
EOF2
    wrap_kiro_stub
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    assert_grep_no_match '\[retry ' "$PANEL_OUT" "v3-style quota error is not retried"
    assert_grep_match '::error::Kiro request quota exhausted' "$PANEL_OUT" "v3-style quota error is reported"
    KIRO_SLOT_BYTES=$(cat "$T_STUB"/work/slot/kiro-*.md 2>/dev/null | wc -c | tr -d ' ')
    assert_eq "0" "$KIRO_SLOT_BYTES" "v3-style quota stdout message is not counted as a response"

    # An exhausted overage allowance is also non-transient, even with exit 0.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
printf 'attempt\n' >> "$0.overage-review-attempts"
printf '%s\n' 'ServiceQuotaExceededException: You have reached the limit for overages.' >&2
exit 0
EOF2
    wrap_kiro_stub
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    OVERAGE_ATTEMPTS=$(wc -l < "$T_STUB/kiro-cli.overage-review-attempts" | tr -d ' ')
    assert_eq "2" "$OVERAGE_ATTEMPTS" "overage exhaustion stops after one review call per Kiro model"
    assert_grep_no_match '\[retry ' "$PANEL_OUT" "overage exhaustion does not consume cell retries"
    assert_file_exists "$T_STUB/work/kiro-quota.flag" "overage exhaustion uses the existing quota diagnostic flag"
    OVERAGE_DETAIL=$(cat "$T_STUB/work/kiro-quota.flag" 2>/dev/null || true)
    assert_contains "$OVERAGE_DETAIL" "You have reached the limit for overages." \
        "overage diagnostic retains the actual account-limit reason"
    assert_grep_no_match '\[quota\].*monthly|::error::Kiro monthly' "$PANEL_OUT" \
        "overage exhaustion is not mislabeled as a monthly limit"
    assert_file_exists "$T_STUB/work/coverage-severe.flag" "overage exhaustion retains the coverage failure gate"

    # Partial review output cannot override an account-limit diagnostic on stderr.
    for QUOTA_CASE in monthly overage; do
        case "$QUOTA_CASE" in
            monthly) QUOTA_MESSAGE='Monthly request limit reached' ;;
            overage) QUOTA_MESSAGE='ServiceQuotaExceededException: You have reached the limit for overages.' ;;
        esac
        printf '%s\n' "$QUOTA_MESSAGE" > "$T_STUB/kiro-cli.partial-quota-message"
        : > "$T_STUB/kiro-cli.partial-quota-attempts"
        cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
printf 'attempt\n' >> "$0.partial-quota-attempts"
printf '%s\n' '> Reviewing the diff...' 'No findings so far.'
cat "$0.partial-quota-message" >&2
exit 0
EOF2
        wrap_kiro_stub
        PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
            bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
        PARTIAL_ATTEMPTS=$(wc -l < "$T_STUB/kiro-cli.partial-quota-attempts" | tr -d ' ')
        assert_eq "2" "$PARTIAL_ATTEMPTS" "$QUOTA_CASE with partial stdout calls each Kiro model once"
        assert_grep_no_match '\[retry ' "$PANEL_OUT" "$QUOTA_CASE with partial stdout is not retried"
        assert_grep_match 'Panel responded \(1 / 3 cells\)' "$PANEL_OUT" \
            "$QUOTA_CASE with partial stdout is excluded from response coverage"
        KIRO_SLOT_BYTES=$(cat "$T_STUB"/work/slot/kiro-*.md 2>/dev/null | wc -c | tr -d ' ')
        assert_eq "0" "$KIRO_SLOT_BYTES" "$QUOTA_CASE with exit 0 discards partial stdout"
        KIRO_FAILED_CELLS=$(printf '%s\n' "$PANEL_OUT" | grep -cE '^\[skip\] kiro-.* \(exit=1\)$' || true)
        assert_eq "2" "$KIRO_FAILED_CELLS" "$QUOTA_CASE with exit 0 records each Kiro cell as failed"
        assert_file_exists "$T_STUB/work/kiro-quota.flag" "$QUOTA_CASE with partial stdout records the quota cause"
        assert_file_exists "$T_STUB/work/coverage-severe.flag" "$QUOTA_CASE with partial stdout keeps coverage blocked"
    done

    # A generic service-quota error can be transient; do not classify its type alone.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
model=unknown
while [ "$#" -gt 0 ]; do
    if [ "$1" = "--model" ]; then model="$2"; break; fi
    shift
done
attempts="$0.transient-$model"
printf 'attempt\n' >> "$attempts"
if [ "$(wc -l < "$attempts")" -eq 1 ]; then
    printf '%s\n' 'ServiceQuotaExceededException: temporary concurrency quota exceeded; retry later.' >&2
    exit 1
fi
echo "no findings"
EOF2
    wrap_kiro_stub
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    TRANSIENT_ATTEMPTS=$(cat "$T_STUB"/kiro-cli.transient-* | wc -l | tr -d ' ')
    assert_eq "4" "$TRANSIENT_ATTEMPTS" "generic transient quota can retry and recover each Kiro cell"
    assert_grep_match 'Panel responded \(3 / 3 cells\)' "$PANEL_OUT" \
        "generic transient quota recovery restores complete coverage"
    TRANSIENT_QUOTA_FLAGS=$(find "$T_STUB/work" -maxdepth 1 -name 'kiro-quota.flag' | wc -l | tr -d ' ')
    assert_eq "0" "$TRANSIENT_QUOTA_FLAGS" "generic quota exception alone does not create an account-limit flag"

    # Overage exhaustion at startup withholds PR input and records the quota cause.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli test"; exit 0; }
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    printf 'attempt\n' >> "$0.overage-preflight-attempts"
    printf '%s\n' 'ServiceQuotaExceededException: You have reached the limit for overages.' >&2
    exit 0
fi
touch "$0.overage-review-started"
echo "no findings"
EOF2
    chmod +x "$T_STUB/kiro-cli"
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    OVERAGE_PREFLIGHT_ATTEMPTS=$(wc -l < "$T_STUB/kiro-cli.overage-preflight-attempts" | tr -d ' ')
    assert_eq "1" "$OVERAGE_PREFLIGHT_ATTEMPTS" "overage exhaustion stops startup before the second Kiro model"
    OVERAGE_REVIEWS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.overage-review-started' | wc -l | tr -d ' ')
    assert_eq "0" "$OVERAGE_REVIEWS" "overage preflight failure never sends PR input to Kiro review cells"
    assert_file_exists "$T_STUB/work/kiro-preflight.flag" "overage preflight failure retains startup diagnostics"
    assert_file_exists "$T_STUB/work/kiro-quota.flag" "overage preflight failure records the specific quota cause"
    assert_file_exists "$T_STUB/work/coverage-severe.flag" "overage preflight failure keeps required coverage blocked"

    # Default-agent fallback invalidates plausible output even when the CLI exits 0.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
echo "Error: no agent with name pr-review-notools found. Falling back to user specified default" >&2
echo "> no findings"
exit 0
EOF2
    wrap_kiro_stub
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    assert_grep_match '::error::kiro-cli ignored --agent pr-review-notools' "$PANEL_OUT" "agent fallback is reported as ::error::"
    assert_grep_no_match 'Panel responded.*kiro-' "$PANEL_OUT" "agent-fallback responses are not counted"
    assert_file_exists "$T_STUB/work/kiro-agent-fallback.flag" "agent fallback leaves kiro-agent-fallback.flag"
    assert_file_exists "$T_STUB/work/coverage-severe.flag" "agent fallback forces coverage-severe"

    # A healthy run must clear old diagnostics and avoid false positives.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
echo "> no findings"
EOF2
    wrap_kiro_stub
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    assert_grep_match 'Panel responded \(3 / 3 cells\)' "$PANEL_OUT" "healthy kiro cells are counted"
    # Use find for a valid zero count; unmatched ls would fail under the TAP runner.
    HEALTHY_FLAGS=$(find "$T_STUB/work" -maxdepth 1 -name '*.flag' | wc -l | tr -d ' ')
    assert_eq "0" "$HEALTHY_FLAGS" "healthy run leaves no flags (stale quota/fallback flags reset)"
    assert_file_exists "$T_STUB/work/kiro-cwd/kiro-opus-L2/.kiro/agents/pr-review-notools.json" \
        "the no-tools agent is copied into the cell cwd (HOME) before kiro-cli runs"

    # Codex can echo reviewed text to stderr; Kiro-only signatures must not discard it or suppress retry.
    cat > "$T_STUB/codex" <<'EOF2'
#!/bin/bash
cat >&2
echo "no findings"
EOF2
    printf 'diff --git a/x b/x\n+Monthly request limit reached\n+You have reached the limit for overages.\n+no agent with name pr-review-notools found\n' > "$T_STUB/diff.txt"
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    assert_grep_match 'Panel responded \(3 / 3 cells\)' "$PANEL_OUT" \
        "Codex quoting Kiro errors remains a successful response"
    QUOTED_FLAGS=$(find "$T_STUB/work" -maxdepth 1 -name '*.flag' | wc -l | tr -d ' ')
    assert_eq "0" "$QUOTED_FLAGS" "quoted Kiro errors in Codex stderr leave no flags"

    cat > "$T_STUB/codex" <<'EOF2'
#!/bin/bash
cat >/dev/null
printf 'attempt\n' >> "$0.attempts"
if [ "$(wc -l < "$0.attempts")" -eq 1 ]; then
    echo "Reviewed code quotes: Monthly request limit reached" >&2
    exit 1
fi
echo "no findings"
EOF2
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    CODEX_ATTEMPTS=$(wc -l < "$T_STUB/codex.attempts" | tr -d ' ')
    assert_eq "2" "$CODEX_ATTEMPTS" "Codex retries its own transient failure despite a quoted Kiro quota"
    assert_grep_match 'Panel responded \(3 / 3 cells\)' "$PANEL_OUT" "Codex retry can restore full coverage"
    RETRY_FLAGS=$(find "$T_STUB/work" -maxdepth 1 -name '*.flag' | wc -l | tr -d ' ')
    assert_eq "0" "$RETRY_FLAGS" "a recovered Codex retry leaves no Kiro failure flags"

    # Both fixed canary checks must finish before review; neither prompt nor stdin may include PR input.
    cat > "$T_STUB/codex" <<'EOF2'
#!/bin/bash
cat >/dev/null
echo "no findings"
EOF2
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli test"; exit 0; }
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    printf 'preflight\n' >> "$0.events"
    cat >> "$0.preflight-input"
    [[ "$2" == *PR_DIFF_MARKER* ]] && touch "$0.diff-in-preflight"
    echo "> NO_TOOLS"
else
    printf 'review\n' >> "$0.events"
    echo "no findings"
fi
EOF2
    printf 'diff --git a/x b/x\n+PR_DIFF_MARKER\n' > "$T_STUB/diff.txt"
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    PREFLIGHT_ORDER=$(head -2 "$T_STUB/kiro-cli.events" | tr '\n' ' ')
    assert_eq "preflight preflight " "$PREFLIGHT_ORDER" "both model preflights finish before any Kiro review"
    PREFLIGHT_INPUT=$(cat "$T_STUB/kiro-cli.preflight-input" 2>/dev/null || echo "missing")
    assert_eq "" "$PREFLIGHT_INPUT" "preflight stdin contains no PR diff"
    PREFLIGHT_LEAKS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.diff-in-preflight' | wc -l | tr -d ' ')
    assert_eq "0" "$PREFLIGHT_LEAKS" "preflight prompt contains no PR diff"
    assert_grep_match 'Panel responded \(3 / 3 cells\)' "$PANEL_OUT" "successful preflight preserves full coverage"

    # Reproduce headless model selection and the legacy/default-v2 conflict.
    # Distinct fixture models catch lost --model values in either call path.
    mkdir -p "$T_STUB/classic-config/.claude" "$T_STUB/classic-lenses"
    cat > "$T_STUB/classic-config/.claude/pr-review.local.json" <<'EOF2'
{"panel":{"codex":{"enabled":true},"kiro-opus":{"enabled":true,"model":"claude-fixture-opus"},"kiro-gpt":{"enabled":true,"model":"gpt-fixture"},"kiro-glm":{"enabled":false}}}
EOF2
    echo "Review the complete diff." > "$T_STUB/classic-lenses/FULL.txt"
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli 2.21.4 fixture"; exit 0; }
[ "${1:-}" = chat ] && [ "$#" -ge 2 ] || exit 2
phase=review
[[ "$2" == 'Kiro startup safety check.'* ]] && phase=preflight
shift 2
model=missing agent=missing legacy=no engine=v2 noninteractive=no wrap=missing
while [ "$#" -gt 0 ]; do
    case "$1" in
        --model) model="$2"; shift 2 ;;
        --agent) agent="$2"; shift 2 ;;
        --legacy-ui) legacy=yes; shift ;;
        --agent-engine) engine="$2"; shift 2 ;;
        --no-interactive) noninteractive=yes; shift ;;
        --wrap) wrap="$2"; shift 2 ;;
        *) exit 2 ;;
    esac
done
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$phase" "$model" "$legacy" "$agent" "$noninteractive" "$wrap" "$engine" >> "$0.classic-calls"
if [ "$legacy" != yes ]; then
    printf "[warn] failed to set model '%s': Method not found\n" "$model" >&2
    exit 0
fi
if [ "$engine" != v1 ]; then
    printf 'error: Conflicting options: --legacy-ui cannot be used with --agent-engine=%s. Use --agent-engine=v1 or remove --legacy-ui.\n' "$engine" >&2
    exit 2
fi
if [ "$phase" = preflight ]; then echo "NO_TOOLS"; else echo "no findings"; fi
EOF2
    PANEL_RC=0
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PR_REVIEW_CONFIG_ROOT="$T_STUB/classic-config" \
        PANEL_TIMEOUT=30 PANEL_RETRIES=1 ROLE_REVIEW=1 bash "$PANEL" \
        "$T_STUB/diff.txt" "$T_STUB/classic-lenses" "$T_STUB/classic-work" 2>&1) || PANEL_RC=$?
    assert_eq "0" "$PANEL_RC" "legacy model-selection fixture completes the panel"
    PREFLIGHT_CALLS=$(awk '$1 == "preflight"' "$T_STUB/kiro-cli.classic-calls" | LC_ALL=C sort)
    REVIEW_CALLS=$(awk '$1 == "review"' "$T_STUB/kiro-cli.classic-calls" | LC_ALL=C sort)
    assert_eq $'preflight\tclaude-fixture-opus\tyes\tpr-review-notools\tyes\tnever\tv1\npreflight\tgpt-fixture\tyes\tpr-review-notools\tyes\tnever\tv1' \
        "$PREFLIGHT_CALLS" "both configured model preflights preserve legacy, v1, model and no-tools flags"
    assert_eq $'review\tclaude-fixture-opus\tyes\tpr-review-notools\tyes\tnever\tv1\nreview\tgpt-fixture\tyes\tpr-review-notools\tyes\tnever\tv1' \
        "$REVIEW_CALLS" "both real review calls preserve legacy, v1, model and no-tools flags"
    assert_grep_no_match 'failed to set model|Method not found|Conflicting options' "$PANEL_OUT" \
        "explicit legacy and v1 selection avoid model warnings and engine conflicts"
    assert_eq $'codex/FULL\nkiro-gpt/FULL\nkiro-opus/FULL' \
        "$(LC_ALL=C sort "$T_STUB/classic-work/expected.txt")" \
        "legacy selection retains every configured specialist cell"
    assert_eq $'codex/FULL\nkiro-gpt/FULL\nkiro-opus/FULL' \
        "$(LC_ALL=C sort "$T_STUB/classic-work/responded.txt")" \
        "legacy selection restores complete review coverage after both preflights"
    CLASSIC_FLAGS=$(find "$T_STUB/classic-work" -maxdepth 1 -name '*.flag' | wc -l | tr -d ' ')
    assert_eq "0" "$CLASSIC_FLAGS" "legacy model-selection run leaves no failure or coverage flags"

    # NO_TOOLS does not excuse a simultaneous default-agent fallback diagnostic.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli test"; exit 0; }
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    echo "Error: no agent with name pr-review-notools found. Falling back to user specified default" >&2
    echo "NO_TOOLS"
else
    touch "$0.review-started"
    echo "no findings"
fi
EOF2
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    PREFLIGHT_REVIEWS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.review-started' | wc -l | tr -d ' ')
    assert_eq "0" "$PREFLIGHT_REVIEWS" "fallback during preflight prevents all Kiro reviews"
    assert_file_exists "$T_STUB/work/kiro-preflight.flag" "failed preflight leaves a diagnostic flag"
    assert_file_exists "$T_STUB/work/kiro-agent-fallback.flag" "fallback during preflight leaves kiro-agent-fallback.flag"
    assert_file_exists "$T_STUB/work/coverage-severe.flag" "failed preflight forces coverage failure"
    rm -f "$T_STUB/kiro-cli.review-started"

    # Every configured model must pass; one canary read withholds all Kiro reviews.
    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli test"; exit 0; }
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    if [[ "$*" == *gpt-5.6-sol* ]]; then
        cat preflight-canary.txt
    else
        echo "NO_TOOLS"
    fi
else
    touch "$0.review-started"
    echo "no findings"
fi
EOF2
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    PREFLIGHT_REVIEWS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.review-started' | wc -l | tr -d ' ')
    assert_eq "0" "$PREFLIGHT_REVIEWS" "a model reading the canary prevents every Kiro review"
    assert_grep_match 'Panel responded \(1 / 3 cells\)' "$PANEL_OUT" "Codex still reviews when Kiro preflight fails"
    rm -f "$T_STUB/kiro-cli.review-started"

    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli test"; exit 0; }
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    echo "NO_TOOLS"
    exit 1
fi
touch "$0.review-started"
echo "no findings"
EOF2
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    PREFLIGHT_REVIEWS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.review-started' | wc -l | tr -d ' ')
    assert_eq "0" "$PREFLIGHT_REVIEWS" "NO_TOOLS with a failed command cannot release PR input"

    cat > "$T_STUB/kiro-cli" <<'EOF2'
#!/bin/bash
[ "${1:-}" = "--version" ] && { echo "kiro-cli test"; exit 0; }
touch "$0.chat-invoked"
if [[ "${2:-}" == 'Kiro startup safety check.'* ]]; then
    echo "NO_TOOLS"
else
    echo "no findings"
fi
EOF2
    PANEL_OUT=$(PATH="$T_STUB:$PATH" PANEL_TIMEOUT=30 PANEL_RETRIES=3 \
        bash "$PANEL" "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1 || true)
    RECOVERED_FLAGS=$(find "$T_STUB/work" -maxdepth 1 -name '*.flag' | wc -l | tr -d ' ')
    assert_eq "0" "$RECOVERED_FLAGS" "a later healthy run clears the failed preflight flags"
    rm -f "$T_STUB/kiro-cli.chat-invoked"

    # Reject duplicate JSON keys before contacting models; the fixture mirrors the helper-relative paths.
    mkdir -p "$T_STUB/fixture/scripts/pr-review/agents" \
      "$T_STUB/fixture/plugins/co-agent/skills/pr-autofix/scripts"
    cp "$PANEL" "$T_STUB/fixture/scripts/pr-review/run-panel.sh"
    cp scripts/pr-review/lib.sh scripts/pr-review/panel_config.py scripts/pr-review/pr-review.defaults.json \
      "$T_STUB/fixture/scripts/pr-review/"
    cp plugins/co-agent/skills/pr-autofix/scripts/review_format.py \
      "$T_STUB/fixture/plugins/co-agent/skills/pr-autofix/scripts/"
    cat > "$T_STUB/fixture/scripts/pr-review/agents/pr-review-notools.json" <<'EOF2'
{"name":"pr-review-notools","tools":[],"tools":["read"],"allowedTools":[],"mcpServers":{},"resources":[],"useLegacyMcpJson":false}
EOF2
    PANEL_RC=0
    PANEL_OUT=$(PATH="$T_STUB:$PATH" bash "$T_STUB/fixture/scripts/pr-review/run-panel.sh" \
        "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1) || PANEL_RC=$?
    assert_eq "1" "$PANEL_RC" "duplicate JSON keys are rejected before startup"
    assert_grep_match 'invalid no-tools agent configuration' "$PANEL_OUT" "the agent-config rejection names its cause"
    CHAT_CALLS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.chat-invoked' | wc -l | tr -d ' ')
    assert_eq "0" "$CHAT_CALLS" "invalid agent configuration never reaches a model"

    cat > "$T_STUB/cp" <<'EOF2'
#!/bin/bash
exit 1
EOF2
    chmod +x "$T_STUB/cp"
    PANEL_RC=0
    PANEL_OUT=$(PATH="$T_STUB:$PATH" bash "$PANEL" \
        "$T_STUB/diff.txt" "$T_STUB/lenses" "$T_STUB/work" 2>&1) || PANEL_RC=$?
    assert_eq "1" "$PANEL_RC" "failed agent copy aborts before startup"
    CHAT_CALLS=$(find "$T_STUB" -maxdepth 1 -name 'kiro-cli.chat-invoked' | wc -l | tr -d ' ')
    assert_eq "0" "$CHAT_CALLS" "failed agent copy never reaches a model"
    rm -rf "$T_STUB"
else
    pass "run-panel.sh quota/fallback stub behaviour (skipped: timeout(1) not available)"
fi
