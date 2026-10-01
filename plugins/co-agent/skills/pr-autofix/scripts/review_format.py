"""A deliberately small presentation contract, not a Markdown or code parser."""

import re
import argparse
from pathlib import Path
import sys


FORMAT_INSTRUCTIONS = (
    "Use English prose. Inline backticks are only for single-line, whitespace-free "
    "symbol/path references (an empty () suffix is allowed). Put all executable "
    "or configuration examples in closed top-level fenced code blocks, starting "
    "and ending on their own lines at column one. Use a longer outer fence if the example contains "
    "a fence. Do not nest example fences in lists or blockquotes. Use synthetic "
    "values only; never copy credentials. Unsupported examples fail review coverage."
    " Sensitive-key assignments outside fences are rejected; ordinary sentences "
    "and path citations remain prose."
)

ERROR_CODE = "unsupported_review_format"
FENCE = re.compile(r"(`{3,}|~{3,})([^\r\n]*)$")
REFERENCE = re.compile(r"(?:[\w./:$@#*+\[\]\\-]+(?:\(\))?)\Z", re.UNICODE)
TICKS = re.compile(r"`+")
ASSIGNMENT_TAIL = re.compile(r"(?P<spacing>\s*)(?P<operator>[:=])")
RHS_WORDS = re.compile(
    r"[ \t]*(?P<first>[^ \t\r\n]+)?"
    r"(?:[ \t]+(?P<second>[^ \t\r\n]+))?"
    r"(?:[ \t]+(?P<third>[^ \t\r\n]+))?"
)
LINK_VALUE = re.compile(r"\[[^\"'\]\r\n]+\]\(")
SETEXT_TAIL = re.compile(r"=*[ \t]*(?:\r?\n|\Z)")
LINE_NUMBER = re.compile(r"L?[0-9]+(?::[0-9]+|-L?[0-9]+)?(?=\Z|[\s)\],.;])")
# Legacy shell adapters have no shared Python credential policy. Structured
# adapters pass their existing sensitive-key pattern explicitly instead.
DEFAULT_SENSITIVE_KEY = (
    r"(?i:(?<![A-Za-z0-9])[A-Za-z0-9_.:-]*(?:password|passwd|pwd|dsn|api[_-]?key|"
    r"secret|token|credential|passphrase|private[_-]?key|cookie|authorization|auth(?![A-Za-z])|dockerconfigjson|"
    r"connection[_-]?string|origin[_-]?verify|AccessKeyId|access[_-]?key[_-]?id|external[_-]?id)[A-Za-z0-9_.:-]*)"
)
DEFAULT_PATTERN = re.compile(DEFAULT_SENSITIVE_KEY)
# Mirror the default key alphabet; other alphabets require a trusted opt-in.
KEY_TOKEN = re.compile(r"[A-Za-z0-9_.:-]+", re.I)
QUOTED_ASSIGNMENT_TAIL = re.compile(r"""(?:\\?["'])?""" + ASSIGNMENT_TAIL.pattern)


def uses_default_pattern(pattern):
    return pattern.pattern == DEFAULT_PATTERN.pattern and pattern.flags == DEFAULT_PATTERN.flags


def token_matcher(pattern, explicit=None):
    if explicit is not None:
        return re.compile(explicit)
    return KEY_TOKEN if uses_default_pattern(pattern) else None


def sensitive_reference(reference, pattern, key_token_pattern=None):
    tokens = token_matcher(pattern, key_token_pattern)
    if tokens is not None:
        return any(pattern.fullmatch(reference, token.start(), token.end())
                   for token in tokens.finditer(reference))
    return pattern.search(reference)


def assignment_matches(text, pattern, key_token_pattern=None):
    """Locate an operator before classifying a key under a declared alphabet."""
    tokens = token_matcher(pattern, key_token_pattern)
    if tokens is None:
        combined = re.compile(pattern.pattern + r"""(?:\\?["'])?""" + ASSIGNMENT_TAIL.pattern,
                              pattern.flags)
        for match in combined.finditer(text):
            yield match.start(), match
        return
    consumed = 0
    for token in tokens.finditer(text):
        start, end = max(token.start(), consumed), token.end()
        if start >= end:
            continue
        tail = QUOTED_ASSIGNMENT_TAIL.match(text, end)
        key_end = end
        if tail is None:
            # When colons belong to the alphabet, the old greedy matcher picks
            # the last one if no operator follows the complete token.
            key_end = text.rfind(":", start, end)
            if key_end < 0:
                continue
            tail = ASSIGNMENT_TAIL.match(text, key_end)
        if pattern.fullmatch(text, start, key_end):
            yield start, tail
            consumed = tail.end()


def is_assignment(text, match, quoted_key=False):
    """A bare section label or Setext underline contains no assignment value."""
    if match["operator"] == ":":
        if quoted_key:
            return True
        words = RHS_WORDS.match(text, match.end())
        first = words["first"] or ""
        if not words["second"] and re.fullmatch(r"[*_~]*", first):
            return False
        if first and LINK_VALUE.match(text, words.start("first")):
            return False  # A prose label may introduce a Markdown reference.
        if first.startswith(("'", '"', "{", "[", "!", "&")):
            return True
        if first.lower() in ("basic", "bearer") and words["second"] and not words["third"]:
            return True
        if first.endswith((".", "!", "?")):
            return False  # A punctuated colon sentence remains prose.
        # Natural-language clauses are not configuration values. Bare atomic
        # values remain a supported assignment spelling; this is not a parser.
        return words["second"] is None
    if (match["operator"] == "=" and any(c in match["spacing"] for c in "\r\n")
            and SETEXT_TAIL.match(text, match.end())):
        return False
    return True


def diagnostic(rule, line=None):
    return {"code": ERROR_CODE, "rule": rule, "line": line}


def format_diagnostic(text, sensitive_pattern=DEFAULT_SENSITIVE_KEY, *, key_token_pattern=None):
    """Return static rule metadata; never include external text in diagnostics.

    Only explicit markup and sensitive assignments are classified. Ordinary
    unmarked prose is not parsed as a programming language. Callers supply the
    existing confidentiality policy's sensitive-key regex when they have one;
    legacy shell adapters use the default pattern above.

    Trusted callers may opt in with key_token_pattern: maximal, nonempty runs
    of their sensitivity pattern's consuming key alphabet, with matching flags.
    Quotes, equals signs and line breaks must remain delimiters. Spaces/tabs may
    belong to the declared alphabet. This is caller code, never model input;
    custom alphabets are not inferred. Without it, custom patterns keep the
    original matcher.
    """
    sensitive_pattern = re.compile(sensitive_pattern)
    fence = None
    fence_line = None
    prose = []
    offset = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        line_start = offset
        offset += len(line)
        body = line.rstrip("\r\n")
        marker = FENCE.fullmatch(body)
        if fence is not None:
            if (marker and marker[1][0] == fence[0]
                    and len(marker[1]) >= len(fence) and not marker[2].strip()):
                fence = None
                prose.append("\0")
            continue
        if marker:
            if not re.fullmatch(r"[A-Za-z0-9_.+-]*[ \t]*", marker[2]):
                return diagnostic("invalid_fence_info", line_number)
            fence = marker[1]
            fence_line = line_number
            prose.append("\0")
            continue
        # Container/indented fences are outside this contract. Delimiter escapes
        # do not opt code examples back into inline syntax.
        if re.search(r"`{3,}|~{3,}", body):
            return diagnostic("nested_or_indented_fence", line_number)
        markers = list(TICKS.finditer(body))
        if len(markers) % 2:
            return diagnostic("unpaired_inline_delimiter", line_number)
        cursor = 0
        for opening, closing in zip(markers[::2], markers[1::2]):
            if opening[0] != closing[0]:
                return diagnostic("mismatched_inline_delimiter", line_number)
            reference = body[opening.end():closing.start()]
            if not REFERENCE.fullmatch(reference):
                return diagnostic("invalid_inline_reference", line_number)
            # Formatting only the key does not make an unfenced assignment safe.
            following = ASSIGNMENT_TAIL.match(text, line_start + closing.end())
            if (following and sensitive_reference(reference, sensitive_pattern, key_token_pattern)
                    and is_assignment(text, following)):
                return diagnostic("unfenced_sensitive_assignment", line_number)
            prose.append(body[cursor:opening.start()])
            prose.append("\0")
            cursor = closing.end()
        prose.append(body[cursor:] + "\n")
    if fence is not None:
        return diagnostic("unclosed_fence", fence_line)
    prose_text = "".join(prose)
    for start, match in assignment_matches(prose_text, sensitive_pattern, key_token_pattern):
        key = prose_text[start:match.start("spacing")]
        quoted_key = key.endswith(("'", '"'))
        path_key = (any(char in key for char in ".:")
                    or (start and prose_text[start - 1] in "/\\."))
        if (not quoted_key and path_key and match["operator"] == ":"
                and not match["spacing"] and LINE_NUMBER.match(prose_text, match.end())):
            continue  # Only an adjacent numeric path:line suffix is a citation.
        if is_assignment(prose_text, match, quoted_key):
            return diagnostic("unfenced_sensitive_assignment")
    return None


def format_violation(text, sensitive_pattern=DEFAULT_SENSITIVE_KEY, *, key_token_pattern=None):
    result = format_diagnostic(text, sensitive_pattern, key_token_pattern=key_token_pattern)
    return result["code"] if result else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("instructions")
    commands.add_parser("check").add_argument("file", type=Path)
    commands.add_parser("filter")
    args = parser.parse_args()
    if args.command == "instructions":
        print(FORMAT_INSTRUCTIONS)
        return 0
    try:
        text = (sys.stdin.buffer.read().decode("utf-8") if args.command == "filter"
                else args.file.read_text(encoding="utf-8"))
        violation = format_violation(text)
    except (OSError, UnicodeError):
        violation = ERROR_CODE
    if violation:
        print(ERROR_CODE, file=sys.stderr if args.command == "filter" else sys.stdout)
        return 2
    if args.command == "filter":
        # Buffer until validation finishes; rejected source never reaches stdout.
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
