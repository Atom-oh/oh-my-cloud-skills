#!/bin/bash
# Scan for secrets before a git commit.
# Triggered by PreToolUse event (matcher: Bash — every Bash call, so this
# script must gate itself on the command, not run its logic unconditionally).
# Exit 2 to block the commit — Claude Code's PreToolUse only treats exit 2 as
# blocking; exit 1 is non-blocking and would let the commit through silently
# (see plugins/kiro/hooks/pre-commit-review.sh / kiro_review.py for the same
# exit-2 convention already used elsewhere in this repo).
#
# Structural limitation (not fixable from PreToolUse, documented rather than
# silently ignored): a compound command whose OWN execution creates the
# secret content (`gen-secret > f && git add f && git commit`) can't be
# caught here — the file doesn't exist yet at the instant this hook runs,
# before the command executes. The only way to close this specific gap is a
# native `.git/hooks/pre-commit` hook (runs after staging, before the commit
# object is created), which is a separate, bigger change (needs an install
# step, since .git/hooks/ isn't tracked by git) — out of scope for this pass.
#
# Second documented residual: a `cd <other-repo> && ... && git commit` in one
# command changes the target repo the same way `-C` does, but isn't detected
# (see the repo-selector section below for why fail-closed on any `cd` isn't
# the right tradeoff here).

block() {
    echo "[secret-scan] BLOCKED: $1" >&2
    exit 2
}

# jq is required to read the command from stdin JSON (below) — without it,
# CMD falls back to $TOOL_INPUT_COMMAND, which is confirmed EMPTY on every
# real invocation (see the note below), so a missing jq would silently
# disable this entire gate (CMD stays empty, the gate never matches, nothing
# is ever scanned) with no error at all. jq is already a hard dependency of
# notify.sh and the check-doc-sync.sh wiring in this same settings.json, so
# treat its absence here the same way the grep -P probe below treats a
# missing PCRE-capable grep: fail closed rather than silently do nothing —
# BUT only for a command that could plausibly be a commit. This hook's
# matcher is "Bash" with no command filter, so blocking unconditionally on
# missing jq (checked before knowing what the command even is) would block
# EVERY Bash call on a jq-less host — ls, git status, a recovery command —
# not just commit attempts. Without jq to properly parse the JSON, fall
# back to a plain substring check on the raw stdin text: if it doesn't even
# mention "commit" anywhere, this can't be a commit-shaped command (JSON
# string-escaping never hides a plain ASCII word), so let it through
# without needing jq at all; only block when it might be.
HOOK_JSON="$(cat 2>/dev/null)"
if ! command -v jq >/dev/null 2>&1; then
    printf '%s%s' "$HOOK_JSON" "${TOOL_INPUT_COMMAND:-}" | grep -qi commit || exit 0
    block "jq is required to verify whether this command is a commit and is not installed. Install jq."
fi

# Only act on commands that actually commit — this hook's matcher is "Bash"
# with no command filter, so without this gate every unrelated Bash call
# (ls, git status, a restore) pays the cost of this script. Read the command
# from stdin JSON (`.tool_input.command`) — the same delivery mechanism
# already proven working by notify.sh (`.message`) and the check-doc-sync.sh
# wiring in settings.json (`.tool_input.file_path`) elsewhere in this repo.
# $TOOL_INPUT_COMMAND (what the pre-existing remarp PreToolUse hook in
# settings.json reads, and what every round of this hook trusted until now)
# is kept as a fallback for defense-in-depth, but instrumenting this script
# against the real harness confirmed that env var is EMPTY on every actual
# PreToolUse invocation — it has never once fired. stdin JSON is the only
# delivery mechanism confirmed to work.
CMD="$(printf '%s' "$HOOK_JSON" | jq -r '.tool_input.command // empty' 2>/dev/null)"
[ -z "$CMD" ] && CMD="${TOOL_INPUT_COMMAND:-}"

# Deliberately loose: `git.*commit` anywhere in the string, not an
# option-token whitelist. A tighter regex like `git[[:space:]]+([a-z-]+[[:space:]]+)*commit`
# looks precise but is fail-open by construction — it silently never matches
# (and never scans) `git -C /path commit` (a `C` flag), `git -c k=v commit`
# (`.`/`=`), or `--git-dir=... commit` (`/`,`=`), since [a-z-] can't consume
# any of those tokens. Over-matching here only costs an extra scan (safe
# direction); under-matching skips the scan entirely (unsafe). Prefer broad.
[[ "$CMD" =~ git.*commit ]] || exit 0

# The repo-selector detection below (-C, --git-dir, --work-tree, GIT_DIR=,
# GIT_WORK_TREE=, GIT_INDEX_FILE=) must only look at git's GLOBAL options
# from the ONE statement that actually invokes `git ... commit` — not at
# anything after "commit" itself (the subcommand's own argument space: its
# own message, its own `-C <commit>` meaning "reuse this other commit's
# message"), not at an earlier, unrelated statement in the same compound
# command, and not at a standalone "commit" that isn't a git invocation at
# all. Splitting on shell statement separators (&&, ||, ;, |, newline) FIRST
# and then finding the first statement that contains both a standalone
# "git" word and a standalone "commit" word gets all of this right at once:
#   - within that one statement, "commit" can only mean the subcommand
#     (nothing else in a statement shaped like `git <opts> commit <args>`
#     would independently satisfy "standalone git" + "standalone commit"),
#     so cutting the statement at "commit" reliably yields just git's own
#     global-option space — including from a heredoc-built message with its
#     own embedded quote, which defeated an earlier textual-stripping
#     attempt at solving this the same way.
#   - an earlier statement's own flags (`python -m pytest &&`, `git -C
#     /other status &&`) never enter the picture, because they're in a
#     DIFFERENT statement.
#   - "commit" appearing only as a substring of another word (`pre-commit`,
#     `committed.txt`) or as a bare argument to an unrelated command (`echo
#     commit`) doesn't make that statement match at all, since neither
#     satisfies "standalone commit" in the first case, and "echo commit" has
#     no standalone "git" word to pair it with in the second — so the search
#     correctly moves on to the next statement instead of matching there.
# If MORE THAN ONE statement matches, this hook resolves and scans only ONE
# repo-selector target no matter which statement is picked — a second,
# separate `git ... commit` in the same compound command would have its own
# -C (or lack of one) silently never checked. Fail closed on that shape
# instead of guessing which one to trust.
#
# Two things a naive split runs into, both closed by MASKING (replacing
# characters with same-length placeholders, so every position lines up with
# the ORIGINAL string) rather than by removing/stripping text:
#   - A newline is only a REAL statement separator OUTSIDE a heredoc —
#     inside one (`-m "$(cat <<'EOF' ... EOF)"`, exactly how this project's
#     own commit messages are built), every line is DATA, not a new
#     statement, and this project's messages routinely mention "git commit"
#     as a prose example within that data. Split on newline naively and
#     that example line independently satisfies "standalone git" +
#     "standalone commit", counting as a second match and fail-closing on
#     every such commit.
#   - A quoted string can contain the word "commit" as data too, and NOT
#     just inside a heredoc — `NOTE=' commit ' git -C /other commit -m x`
#     has a REAL invocation with its own -C, but the word "commit" inside
#     the single-quoted string comes first in the string, so an unmasked
#     search finds that fake occurrence and cuts there, losing "-C /other"
#     the same way a heredoc's prose example would.
# Masking heredoc bodies and quoted-string interiors before searching
# removes exactly the content that causes both false matches, without
# touching the real invocation characters around them — and because
# masking preserves length/position instead of deleting anything, the
# match position found in the MASKED text is used to slice the ORIGINAL
# (unmasked) text for the actual result, so quoting is never lost from
# what gets returned either.
# python3 -I (not jq, which can't slice a string by a match position) does
# this. Falling back to the untruncated $CMD when python3 isn't available
# was tried and reverted — that re-exposed exactly the false-positive this
# whole design exists to avoid: the repo-selector checks below would then
# run against the ENTIRE command, including an ordinary commit message that
# happens to mention "GIT_DIR=" or "-C " as prose (this project's own
# commit messages routinely do, describing fixes like this one). Falling
# back to an EMPTY string instead means the repo-selector checks find
# nothing and simply don't fire — on a python3-less host, an actual -C/
# --git-dir redirect goes unresolved rather than false-blocking an ordinary
# commit's message text, the same accepted tradeoff already documented for
# the `cd other-repo` residual gap above (unverified rather than
# incorrectly verified).
CMD_SIG=""
if command -v python3 >/dev/null 2>&1; then
    py_out="$(printf '%s' "$CMD" | python3 -I -c '
import sys, re
s = sys.stdin.read()

def mask(text):
    # Pass 1: blank heredoc body lines (same length, using "x" filler).
    line_spans = []
    pos = 0
    for line in text.split("\n"):
        line_spans.append((pos, pos + len(line)))
        pos += len(line) + 1
    out = list(text)
    delim = None
    for (a, b) in line_spans:
        line = text[a:b]
        if delim is not None:
            if line.strip() == delim:
                delim = None
            else:
                for j in range(a, b):
                    out[j] = "x"
            continue
        m = re.search(r"<<-?~?\s*([\x27\"]?)(\w+)\1", line)
        if m:
            delim = m.group(2)
    s1 = "".join(out)
    # Pass 2: blank the INTERIOR of single- and double-quoted strings
    # (quote characters themselves stay, so the block below can still
    # detect and reject a quoted -C argument same as before).
    out2 = list(s1)
    i, n = 0, len(s1)
    while i < n:
        c = s1[i]
        if c == "\x27":
            j = i + 1
            while j < n and s1[j] != "\x27":
                out2[j] = "x"
                j += 1
            i = j + 1
        elif c == "\"":
            j = i + 1
            while j < n and s1[j] != "\"":
                out2[j] = "x"
                j += 1
            i = j + 1
        else:
            i += 1
    return "".join(out2)

masked = mask(s)
# A boundary is whitespace, start/end of string, OR a shell control
# character (&, |, ;, (, ), <, >, `) that can sit directly against a word
# with no space at all — `git init&&git commit`, `(git commit -m a) && (...)`,
# `git commit>/dev/null`, `` `git commit` ``. A plain \s-only boundary
# treats "init" in the first example, "git" in the second, "commit" in the
# third, and both words in the fourth as NOT standalone (no space touches
# them), silently failing to recognize any.
B = r"(?:[\s&|;()<>`]|^|$)"
# `&` must split same as `&&` (a single background-job `&` is also a
# statement separator) — listed before the bare-word alternatives below so
# `&&` still consumes both characters at once, same ordering as `||`/`|`.
# The bare-`&` alternative excludes fd-duplication forms (`2>&1`, `&>file`,
# `1>&2`) via lookaround alone -- `<`/`>` immediately next to the `&` is
# what marks those as redirect tokens rather than a statement separator
# (`2>&1`: `&` preceded by `>`; `&>file`: `&` followed by `>`), never a
# bare digit by itself. An earlier version of this lookbehind also excluded
# a digit immediately before `&`, reasoning it might be part of a redirect
# -- but a real background-job `&` routinely follows ordinary digit-ending
# text too (`git commit -m msg1 & git -C /other commit -m y`), and
# excluding it there silently merged two separate commits back into one
# statement, defeating the multi-commit fail-closed check just below
# (matches=1 instead of 2) and losing the second commit own `-C`.
# `$(` also splits, even with no shell operator between two instances --
# `echo $(git -C /a commit -m x) $(git -C /b commit -m y)` has no &&/;/|
# anywhere (both substitutions are just space-separated ARGUMENTS to
# `echo`), so without this, `(` merely being in `B` let both occurrences
# get counted as ONE unsplit statement -- matches=1 instead of 2, so the
# multi-commit fail-closed check below never fired and the second `-C`
# was silently never verified. A bare `(` (no `$`) is deliberately NOT a
# split point here: `(cmd1) (cmd2)` with no operator between them is not
# valid shell syntax to begin with, so that ambiguity cannot arise; the
# existing `(git commit -m a) && (...)` case already has an explicit `&&`
# splitting it. A `$(` that is itself inside a quoted string or heredoc
# body (how this project own multi-line commit messages are built) is
# already invisible here -- it was replaced with "x" placeholders by the
# masking pass above, long before this split runs.
#
# The same "no operator, just whitespace between two invocations" gap
# applies identically to a backtick substitution and process substitution
# (`<(`/`>(`) -- `` echo `git -C /a commit -m x` `git -C /b commit -m y` ``
# and `cat <(git -C /a commit ...) <(git -C /b commit ...)` are both single
# unsplit statements today for the exact same reason `$(...)  $(...)` was.
# A bare backtick has no "open" vs "close" distinction a regex can tell
# apart, but splitting on EVERY backtick occurrence still gets a single
# substitution right (both halves land on either side of an empty middle
# segment) and correctly separates two side-by-side ones.
seps = [sp.span() for sp in re.finditer(r"&&|\|\||;|\||\n|(?<![<>])&(?![&>])|\$\(|`|<\(|>\(", masked)]
starts = [0] + [e for (_, e) in seps]
ends = [st for (st, _) in seps] + [len(masked)]
matches = []
for (a, b) in zip(starts, ends):
    stmt = masked[a:b]
    if re.search(B + "git" + B, stmt) and re.search(B + "commit" + B, stmt):
        matches.append((a, b))
if len(matches) > 1:
    sys.exit(3)  # more than one separate commit invocation — see bash side
elif matches:
    a, b = matches[0]
    m = re.search(B + "(commit)" + B, masked[a:b])
    sys.stdout.write(s[a:a + m.start(1)])  # slice the ORIGINAL text
else:
    # No statement anywhere in the command has a standalone "git" AND a
    # standalone "commit" word. The FIRST question -- checked before
    # anything else -- is whether the raw text even looks like it names a
    # repo-selector (-C/--git-dir/--work-tree/GIT_DIR=/...). If it does,
    # which repo is actually meant cannot be told apart from text alone, so
    # this fails closed (exit 5) no matter what else is true about the
    # command -- specifically, checked BEFORE the non-commit classification
    # below, not after: a command can hide its own literal "commit" word
    # from a text-based check (quote-splicing like `com''mit`, a variable
    # holding the pieces) while a REAL, literal "-C /somewhere" still sits
    # in the raw text plainly readable, and letting the (mis-classified as
    # "not a commit") case win in that situation would drop the scan
    # entirely instead of failing closed on the selector it can plainly
    # see. Checked against raw `s`, not masked, because masked blanks a
    # selector that is itself quoted (`git "-C" /other "commit" -m x` is
    # valid and really does pass -C to git); a command that reaches this
    # branch is already atypical, so the friction of an occasional prose
    # "-C" mention triggering it is an accepted tradeoff against silently
    # missing a real one.
    #
    # Only once there is no selector hint at all does it matter whether
    # this command is:
    #   (a) genuinely not a commit -- every "commit" in the raw text is
    #       specifically a long-option flag value (`git log
    #       --grep=commit`), never its own word (exit 4). Checked with
    #       `--flag=commit`, not a bare `(?<!=)` character check -- the
    #       latter also (wrongly) classified a commit invoked through a git
    #       alias definition as non-commit. Residual gap this still cannot
    #       close: a command that invokes an ALREADY-defined alias by its
    #       short name (`git c --trailer=commit -m x`, where some earlier,
    #       separate `git config alias.c commit` made "c" mean "commit")
    #       has no literal standalone "commit" word anywhere in THIS
    #       command at all, so nothing here can ever recognize it -- same
    #       class of undecidable-from-static-text limitation as the `cd
    #       other-repo` gap documented near the top of this file.
    #   (b) a REAL commit this parser failed to recognize as standalone --
    #       quoted (`git "commit" -m x`), reached through variable
    #       indirection (`GIT=git; "$GIT" commit -m x`), etc. (exit 6).
    # Bash treats (a) and (b) identically once there is no selector hint --
    # CMD_SIG="" and fall through to the unconditional scan below, rather
    # than skipping the hook outright. An earlier version of (a) skipped
    # the entire hook (bash `exit 0`) on the reasoning that a confirmed
    # non-commit needs no commit-secret scan -- true on its own, but it
    # also skipped this hook OTHER, independent checks that do not
    # depend on this being a commit at all (the force-add-bypasses-
    # .gitignore detection further below), for a command that also force-
    # adds a file alongside an unrelated, non-commit "commit" mention
    # (`git add -f .env && git log --grep=commit`). Falling through here
    # costs the friction round 18 was trying to remove (a confirmed
    # non-commit command can once again fail closed over an unrelated,
    # pre-existing secret already sitting in the working tree) -- accepted
    # again, same as the top-level gate comment above: over-scanning only
    # costs friction, under-scanning misses a real secret.
    # `-C` needs a boundary BEFORE it, not a `\b` word-boundary AFTER it --
    # global -C accepts a concatenated target with no space (`-C/other`,
    # `-Cother`), same as the bash-side extraction regex below handles;
    # `-C\b` requires a non-word character right after the "C", which a
    # concatenated target never has, silently missing that whole form. The
    # boundary class here also carries quote characters -- `git "-C" /other
    # "commit" -m x` is exactly the shape this whole exit-5 branch exists
    # for (quoting hid the standalone "commit" word from the match above),
    # and the quote sitting directly before "-C" is itself the boundary
    # that needs recognizing, or the very case motivating this check slips
    # through it.
    if re.search(r"(?:^|[\s&|;()<>`\"\x27])-C|--git-dir|--work-tree|GIT_DIR=|GIT_WORK_TREE=|GIT_INDEX_FILE=|core\.worktree=", s):
        sys.exit(5)
    flagval_commits = len(re.findall(r"--[A-Za-z][A-Za-z-]*=[\"\x27]?commit\b", s))
    total_commits = len(re.findall(r"\bcommit\b", s))
    if total_commits > 0 and total_commits == flagval_commits:
        sys.exit(4)
    else:
        sys.exit(6)
' 2>/dev/null)"
    py_rc=$?
    if [ "$py_rc" -eq 3 ]; then
        block "command contains more than one separate 'git ... commit' invocation — this hook resolves and scans only one repo-selector target, so a second commit's own -C (or lack of one) is never independently verified. Run each commit as its own Bash call."
    elif [ "$py_rc" -eq 5 ]; then
        block "command may redirect git's target repo (-C/--git-dir/--work-tree/GIT_DIR=/GIT_WORK_TREE=/GIT_INDEX_FILE=/core.worktree=) but this hook could not isolate a single, unambiguous 'git ... commit' statement to verify it against (quoting, or variable/alias indirection). Run the commit as its own plain 'git -C <repo> commit ...' Bash call so this hook can confirm what it's scanning."
    elif [ "$py_rc" -eq 4 ]; then
        # Confirmed non-commit (every "commit" in the text is a flag
        # value) -- no commit-secret scan needed, but NOT a bash `exit 0`:
        # this hook's other, commit-independent checks (force-add-bypasses-
        # .gitignore, further below) must still run for a command that also
        # does something like `git add -f .env` alongside the non-commit
        # "commit" mention. Fall through with no resolved repo-selector.
        CMD_SIG=""
    elif [ "$py_rc" -eq 6 ]; then
        echo "[secret-scan] could not isolate a single git-commit statement (quoting or variable/alias indirection) and no repo-selector token was found in the raw command — scanning this hook's own cwd" >&2
        CMD_SIG=""
    elif [ "$py_rc" -eq 0 ]; then
        CMD_SIG="$py_out"
    else
        # python3 crashed or was killed (rc 1/2, or anything else this
        # chain doesn't name) -- CMD_SIG is already "" from its
        # initialization above, so this isn't a silent fail-open (the
        # unconditional scan below still runs against this hook's own
        # cwd), but unlike the exit-6 case there was no warning at all.
        # Same diagnostic, so this path is visible too.
        echo "[secret-scan] command parser exited unexpectedly (rc=$py_rc) — scanning this hook's own cwd" >&2
    fi
fi

# Repo-selector resolution. `-C <path>` (as a GLOBAL option, in $CMD_SIG —
# see above) runs git against a DIFFERENT repo than this hook's own cwd —
# every git call below must follow it, or a `git -C /other/repo commit`
# matches the gate but scans the wrong repo.
#
# Other redirection forms in $CMD_SIG fail closed rather than being resolved:
# --git-dir/--work-tree (either `=value` or a separate ` value` token),
# GIT_DIR=/GIT_WORK_TREE=/GIT_INDEX_FILE= environment assignments, and more
# than one -C. These are rare enough in practice that fail-closed is the
# right tradeoff.
#
# An EARLIER, UNRELATED `cd` anywhere in the same multi-statement command is
# handled differently — NOT resolved and NOT fail-closed. Claude Code very
# routinely writes commands shaped like `cd <dir>; <unrelated work>; ...;
# git commit ...` (including this very script's own test suite), where
# "commit" only shows up much later. Fail-closed on any `cd` token, however
# broad-in-principle-only, actual-in-practice blocked the overwhelming
# majority of ordinary multi-step Bash calls, not just the narrow "committed
# in a different repo than the session's own cwd" case it was meant to catch.
# Left as a documented residual gap, same treatment as the TOCTOU limitation
# noted at the top of this file: a `cd other-repo && git commit` this hook's
# own cwd doesn't already reflect can still scan the wrong repo.
GIT_C=()
# `git diff`/`git ls-files` always print paths relative to the repo ROOT,
# even when this hook's own cwd is a subdirectory of it — so anchoring
# WORK_DIR to a bare "." and joining it with those root-relative paths
# breaks (double-prefixes the subdirectory) the moment cwd isn't already
# the root. Anchor to the actual root unconditionally, not only when -C
# resolves one; if that lookup itself fails, this hook isn't even inside a
# git repo, matching the "not a git repository" case scan_list_from already
# fails closed on.
WORK_DIR="$(command git rev-parse --show-toplevel 2>/dev/null)"
c_count=$(grep -o -- '-C\b' <<<"$CMD_SIG" 2>/dev/null | wc -l)
HAS_REDIRECT=0
[[ "$CMD_SIG" =~ (^|[[:space:]])-C[[:space:]]*([^[:space:]]+) ]] && HAS_REDIRECT=1
[[ "$CMD_SIG" =~ --git-dir(=|[[:space:]]) ]] && HAS_REDIRECT=1
[[ "$CMD_SIG" =~ --work-tree(=|[[:space:]]) ]] && HAS_REDIRECT=1
[[ "$CMD_SIG" =~ GIT_DIR= ]] && HAS_REDIRECT=1
[[ "$CMD_SIG" =~ GIT_WORK_TREE= ]] && HAS_REDIRECT=1
[[ "$CMD_SIG" =~ GIT_INDEX_FILE= ]] && HAS_REDIRECT=1
[[ "$CMD_SIG" =~ (-c|--config)[[:space:]]+core\.worktree= ]] && HAS_REDIRECT=1
# `-C` immediately preceded by a quote character (`git "-C" /other commit`)
# is real to git once the shell strips the quote, but the extraction above
# only recognizes a plain-whitespace boundary before "-C" and silently
# fails to see this form at all -- fail closed on it explicitly rather than
# letting HAS_REDIRECT stay 0 and this hook fall through to scanning its
# own cwd while the actual commit goes to a repo it never even looked at.
QUOTED_C_ADJACENT=0
[[ "$CMD_SIG" =~ [\"\']-C ]] && QUOTED_C_ADJACENT=1 && HAS_REDIRECT=1

# If this hook's own cwd isn't inside a git repository at all, the command
# doesn't try to point git at one either, and the command does NOT itself
# create one (no standalone "init" word), there is nothing here yet for
# this hook to verify — no repo means no index, no working tree, no secrets
# that could leak, and a bare `git commit` fails on its own outside a repo
# regardless of what this hook does. Blocking that specific shape purely
# because a repo doesn't exist yet would be friction with no security
# benefit.
#
# `git init && git add . && git commit` in the SAME call is a different,
# genuinely dangerous shape this reasoning does NOT cover: init creates the
# repo and the rest of that same call can commit it immediately, with
# whatever files already happen to sit in this directory — this hook's
# enumeration calls have no index yet to consult at the instant it runs, so
# there is no way to scan those files before they're committed. Rather than
# letting that whole compound command through unscanned (which is exactly
# what "no repo → exit 0" would do), fail closed on it: a real secret
# already sitting in the directory when it's freshly `git init`-ed and
# committed in one shot must not go out unscanned.
# This boundary character class, and the two below it (has_add/has_force),
# must stay a superset of the Python `B` class above (`[\s&|;()<>` + backtick]`)
# -- this one additionally carries quote characters, since a bare-word
# check on raw $CMD has no prior masking pass to already neutralize a
# quoted "init"/"add"/"-f".
if [ -z "$WORK_DIR" ]; then
    if [[ "$CMD" =~ (^|[[:space:]\&\|\;\(\)\<\>\`\"\'])init([[:space:]\&\|\;\(\)\<\>\`\"\']|$) ]]; then
        block "command both initializes a repository and commits in the same call — this hook has no index yet to scan whatever files already exist in this directory before they're committed. Run 'git init' as its own Bash call first, then commit separately once a repository (and therefore a scannable index) exists."
    fi
    if [ "$HAS_REDIRECT" -eq 0 ]; then
        exit 0
    fi
fi
[ -z "$WORK_DIR" ] && WORK_DIR="."

if [ "${c_count:-0}" -gt 1 ] || [ "$QUOTED_C_ADJACENT" -eq 1 ] || \
   [[ "$CMD_SIG" =~ --git-dir(=|[[:space:]]) ]] || \
   [[ "$CMD_SIG" =~ --work-tree(=|[[:space:]]) ]] || [[ "$CMD_SIG" =~ GIT_DIR= ]] || \
   [[ "$CMD_SIG" =~ GIT_WORK_TREE= ]] || [[ "$CMD_SIG" =~ GIT_INDEX_FILE= ]] || \
   [[ "$CMD_SIG" =~ (-c|--config)[[:space:]]+core\.worktree= ]]; then
    block "command redirects git's target repo in a form this hook doesn't verify (--git-dir/--work-tree/GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE/core.worktree/multiple -C/quote-adjacent -C). Run the commit as its own 'git -C <repo> commit ...' call, or from that repo's own directory, so this hook can confirm what it's scanning."
fi
if [[ "$CMD_SIG" =~ (^|[[:space:]])-C[[:space:]]*([^[:space:]]+) ]]; then
    raw_target="${BASH_REMATCH[2]}"
    case "$raw_target" in
        *\"*|*\'*) block "could not reliably parse the -C argument (quoted path) in: $CMD" ;;
    esac
    resolved="$(command git -C "$raw_target" rev-parse --show-toplevel 2>/dev/null)"
    if [ -z "$resolved" ]; then
        block "-C target '$raw_target' is not a git repository (or doesn't exist)."
    fi
    GIT_C=(-C "$resolved")
    WORK_DIR="$resolved"
fi
git() { command git "${GIT_C[@]}" "$@"; }

SECRETS_FOUND=0

# grep -P (PCRE) is required below — probe it once and fail CLOSED (block the
# commit, not every Bash call — see the gate above) if unsupported, e.g. BSD/
# macOS grep has no -P at all.
if ! printf 'x' | grep -qP 'x' 2>/dev/null; then
    block "this system's grep does not support -P (PCRE), so secrets cannot be reliably scanned before commit. Install GNU grep."
fi

# Patterns to detect. No lookbehind: GNU grep's PCRE backend rejects
# variable-length lookbehind (e.g. \s{0,5} inside (?<=...)) with "lookbehind
# assertion is not fixed length" — silently swallowed by a `2>/dev/null`
# guard, which would let a pattern shaped that way never actually match.
# Matching the context inline (no lookbehind) works for boolean detection
# since we only need grep -q, not the matched substring. -i (case-insensitive)
# below covers e.g. `Password=`/`API_KEY=` env-var-style assignments too.
#
# Split into two confidence tiers: HIGH_CONFIDENCE_PATTERNS are fixed-prefix
# service-key formats (a real AKIA/sk-ant-/ghp_ value is essentially never a
# placeholder) — these are the ones still worth checking even in a file
# that's SUPPOSED to hold only placeholders. GENERIC_PATTERNS (bare
# password=/secret=/api_key= assignments) are exactly the shapes a
# placeholder itself commonly takes (`API_KEY=your-key-here`), so applying
# them to a template file would be mostly false positives.
HIGH_CONFIDENCE_PATTERNS=(
    'AKIA[0-9A-Z]{16}'                                    # AWS Access Key ID
    'ASIA[0-9A-Z]{16}'                                    # AWS temporary/STS Access Key ID
    'aws_secret_access_key\s{0,5}[=:]\s{0,5}["\x27]?[A-Za-z0-9/+=]{40}' # AWS Secret Key (context-aware; optional quote before the value — a bare `[=:]` with no quote allowance misses the common `KEY="value"` .env style entirely)
    'sk-proj-[A-Za-z0-9_-]{20,}'                          # OpenAI API Key (project format)
    'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'           # OpenAI API Key (legacy format)
    'sk-ant-[A-Za-z0-9-]{90,}'                            # Anthropic API Key
    'ghp_[A-Za-z0-9]{36}'                                 # GitHub Personal Access Token
    'gho_[A-Za-z0-9]{36}'                                 # GitHub OAuth Token
    'github_pat_[A-Za-z0-9_]{82}'                         # GitHub Fine-grained PAT
    'xoxb-[0-9]+-[A-Za-z0-9]+'                            # Slack Bot Token
    'xoxp-[0-9]+-[A-Za-z0-9]+'                            # Slack User Token
    'sk_live_[A-Za-z0-9]{24,}'                            # Stripe Secret Key
    'rk_live_[A-Za-z0-9]{24,}'                            # Stripe Restricted Key
    'AIza[A-Za-z0-9_-]{35}'                               # Google API Key
    'ya29\.[A-Za-z0-9_-]{50,}'                            # Google OAuth Token
    'DefaultEndpointsProtocol=https;Account'              # Azure Connection String
)
# This repo's own review checklist for this class of hook names Kiro and
# Antigravity keys explicitly by service — worth checking even in the
# template file, unlike the fully generic password=/secret=/api_key=
# assignments below (which are exactly the shape a PLACEHOLDER commonly
# takes, e.g. `API_KEY=your-key-here`, so applying them to a file meant to
# hold placeholders would be mostly false positives). These two have no
# fixed-format value to anchor on the way AKIA/sk-ant-/ghp_ do, so they
# still carry some of that same placeholder-matching risk — but it's a
# service-specific variable name, not a generic one, so the blast radius
# is far narrower.
PROJECT_KEY_PATTERNS=(
    'kiro_api_key\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'        # Kiro API Key
    'antigravity_api_key\s*[:=]\s*["\x27]?[^\s"\x27]{8,}' # Antigravity API Key
)
GENERIC_PATTERNS=(
    'password\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'            # Password assignments
    'secret\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'              # Secret assignments
    'api[_-]?key\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'         # API key assignments
)
PATTERNS=("${HIGH_CONFIDENCE_PATTERNS[@]}" "${PROJECT_KEY_PATTERNS[@]}" "${GENERIC_PATTERNS[@]}")

# Fully skipped — the exact path, since `[[ "$file" == $pattern ]]` matches
# the whole staged path and a bare filename would also exempt any unrelated
# file sharing that name elsewhere. Only this script's own file is a TRUE
# full skip: its source contains every detection pattern above as a literal
# string, so scanning it against its own patterns risks self-matching.
# package-lock.json/yarn.lock are NOT fully skipped (below) — a private
# registry's resolved URL can still carry a fixed-prefix token
# (ghp_/sk-.../AKIA...) that HIGH_CONFIDENCE_PATTERNS catches regardless of
# surrounding URL syntax (an opaque, non-fixed-format credential embedded as
# `https://user:token@...` is NOT covered by any pattern here); only the
# noisy GENERIC_PATTERNS (password=/secret=/api_key=, which a lockfile has
# no legitimate reason to contain anyway) are skipped for them.
SKIP_FILES=('.claude/hooks/secret-scan.sh')

# tests/pr-review/{test-lib,test-synthesize}.sh deliberately embed fake-credential
# literals (AKIA.../sk-proj-.../ghp_...) as scrub_secrets() fixtures. A full-file skip
# (an earlier version of this list) would make those files a permanent secret-scanning
# blind spot — a REAL credential pasted into one later would never be caught. Instead,
# strip only these exact known-fake literal strings before scanning those files, so
# anything else in them still goes through the normal patterns below. One shared list —
# both files draw from the same small fake-credential vocabulary.
PR_REVIEW_TEST_FIXTURE_LITERALS=(
    'AKIAABCDEFGHIJKLMNOP'
    'ASIAABCDEFGHIJKLMNOP'
    'ghp_abcdefghijklmnopqrstuvwxyz1234'
    'xoxb-1234567890-abcdefghij'
    'sk-proj-abcdefghijklmnopqrstuvwxyz'
    'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234'
    'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    'abcdefghijklmnop'
    'supersecretvalue123'
    'get_secret()'
)

# Remove each literal exactly once per occurrence (bash's `//` is global) —
# what's left is scanned normally below, so a REAL secret added anywhere
# else in the file (or replacing one of these placeholders with a live
# value) still matches PATTERNS.
strip_pr_review_test_fixtures() {
    local content="$1" lit
    for lit in "${PR_REVIEW_TEST_FIXTURE_LITERALS[@]}"; do
        content="${content//$lit/}"
    done
    printf '%s' "$content"
}

is_skipped() {
    local f="$1" s
    for s in "${SKIP_FILES[@]}"; do
        [ "$f" = "$s" ] && return 0
    done
    return 1
}

scan_content() {
    local file="$1" content="$2" regex
    case "$file" in
        # scrub_secrets() fixture files — strip only the known-fake literal
        # values (see PR_REVIEW_TEST_FIXTURE_LITERALS above), then fall
        # through to the normal full-PATTERNS scan below on what's left.
        tests/pr-review/test-lib.sh|*/tests/pr-review/test-lib.sh| \
        tests/pr-review/test-synthesize.sh|*/tests/pr-review/test-synthesize.sh)
            content="$(strip_pr_review_test_fixtures "$content")"
            ;;
    esac
    case "$file" in
        # Anchored to the basename boundary (`*/name` or bare `name`, not a
        # bare `*name` suffix glob) — `*package-lock.json` would also match
        # an unrelated `credentials-package-lock.json`.
        *.env.example|package-lock.json|*/package-lock.json|yarn.lock|*/yarn.lock)
            for regex in "${HIGH_CONFIDENCE_PATTERNS[@]}" "${PROJECT_KEY_PATTERNS[@]}"; do
                if printf '%s' "$content" | grep -qPi "$regex" 2>/dev/null; then
                    echo "[secret-scan] Potential secret found in $file (pattern: ${regex:0:30}...)"
                    SECRETS_FOUND=1
                fi
            done
            return
            ;;
    esac
    for regex in "${PATTERNS[@]}"; do
        if printf '%s' "$content" | grep -qPi "$regex" 2>/dev/null; then
            echo "[secret-scan] Potential secret found in $file (pattern: ${regex:0:30}...)"
            SECRETS_FOUND=1
        fi
    done
}

# A failed enumeration/read must not silently read as "nothing to scan" —
# this is a blocking security gate, so "couldn't verify" fails the same way
# "found a secret" does. Using a real temp file (not process substitution)
# so the git command's own exit status is directly checkable.
TMP_LIST="$(mktemp)"
trap 'rm -f "$TMP_LIST"' EXIT

scan_list_from() {
    # $1: description (for the error message)  $2..: the git/ls-files argv
    local desc="$1"; shift
    if ! "$@" > "$TMP_LIST" 2>/dev/null; then
        block "could not enumerate $desc — refusing to commit without a verified scan."
    fi
    while IFS= read -r -d '' file; do
        is_skipped "$file" && continue
        case "$desc" in
            staged*)
                local content
                content="$(git show ":$file" 2>/dev/null)" || block "could not read staged content of '$file' to scan it."
                scan_content "$file" "$content"
                ;;
            *)
                [ -f "$WORK_DIR/$file" ] || continue
                local content
                content="$(cat "$WORK_DIR/$file" 2>/dev/null)" || block "could not read '$file' to scan it."
                scan_content "$file" "$content"
                ;;
        esac
    done < "$TMP_LIST"
}

# Staged (index) content — `--diff-filter=ACMRT` includes renames (a rename
# that also modifies content still shows up here) and typechanges (e.g. a
# symlink replaced by a regular file carrying a secret).
scan_list_from "staged files" git diff --cached -z --name-only --diff-filter=ACMRT

# Always also scan the working tree + untracked files, not just the index.
# PreToolUse fires BEFORE the command runs, so at the instant this scan
# happens the index reflects the state *before* whatever this same command is
# about to do — `git add -A && git commit`, `-a`/`-am`/`--all`, `--only`/
# `--include <path>`, a bare pathspec commit (`git commit -m msg file.txt`),
# or short flags (`-i`/`-o`) all stage/commit working-tree content that a
# staged-only scan would never see. Rather than maintain a flag-token
# whitelist for "does this commit form touch the working tree" (which is how
# three rounds of review kept finding one more missed form — `-C`, `--only`,
# pathspec, `-i`/`-o`), always scan both: the cost of scanning working-tree/
# untracked content on a commit that turns out to be `git commit` with
# nothing further is one extra (cheap) pass, not a bypass.
scan_list_from "working-tree changes" git diff -z --name-only --diff-filter=ACMRT

# Untracked, non-ignored files. `git ls-files -z` is NUL-delimited by git
# itself, unlike piping `git status --porcelain -z` through `awk
# 'BEGIN{RS="\0"}'` — mawk (Debian/Ubuntu default) and BSD awk (macOS) don't
# reliably support NUL record separators, so that pipeline could silently
# produce nothing on those systems: a fail-open with no error.
scan_list_from "untracked files" git ls-files -z --others --exclude-standard

# `git add -f`/`--force` (including combined short flags like `-Af`, and
# with global options like `-C .` between `git` and `add`) overrides
# .gitignore, so a command shaped that way can stage (and this commit can
# then commit) a file the scan above deliberately excludes as ignored. Only
# check this narrower, ignored-only list when the command actually shows
# add+force together — it can be large in a repo with big ignored trees
# (node_modules, build/), so it's not worth always paying for. `add` and the
# force flag are checked independently (not `git[[:space:]]+add` as one
# token) so `git -C . add -f` still counts — over-matching here only costs
# an extra scan.
# Residual, documented gap in these two checks (same class as the `cd
# other-repo` and alias gaps noted elsewhere in this file): they match
# against raw $CMD with no masking pass, so a quote-split flag
# (`-''f`, `a''dd`) that bash still executes as `-f`/`add` is invisible to
# `[a-zA-Z]*` here the same way it is to the Python side's literal-word
# checks. Undecidable from this kind of text-only matching without porting
# this check onto the already-masked Python text, which would need a new
# exit code and CMD_SIG-style channel back to bash -- not done here.
has_add=0; has_force=0
[[ "$CMD" =~ (^|[[:space:]\&\|\;\(\)\<\>\`\"\'])add([[:space:]\&\|\;\(\)\<\>\`\"\']|$) ]] && has_add=1
{ [[ "$CMD" =~ [[:space:]\&\|\;\(\)\<\>\`\"\']-[a-zA-Z]*f[a-zA-Z]*([[:space:]\&\|\;\(\)\<\>\`\"\']|$) ]] || \
  [[ "$CMD" =~ --force([[:space:]\&\|\;\(\)\<\>\`\"\']|$) ]]; } && has_force=1
if [ "$has_add" -eq 1 ] && [ "$has_force" -eq 1 ]; then
    scan_list_from "force-added ignored files" git ls-files -z --others -i --exclude-standard
fi

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo "[secret-scan] BLOCKED: Potential secrets detected."
    echo "[secret-scan] Review the files above and remove secrets before committing."
    echo "[secret-scan] Use .env files for secrets and .env.example for templates."
    exit 2
fi
