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
# Legacy shell adapters have no shared Python credential policy. Structured
# adapters pass their existing sensitive-key pattern explicitly instead.
DEFAULT_SENSITIVE_KEY = (
    r"(?i:(?<![A-Za-z0-9])[A-Za-z0-9_.:-]*(?:password|passwd|pwd|dsn|api[_-]?key|"
    r"secret|token|credential|passphrase|private[_-]?key|cookie|authorization|auth(?![A-Za-z])|dockerconfigjson|"
    r"connection[_-]?string|origin[_-]?verify|AccessKeyId|access[_-]?key[_-]?id|external[_-]?id)[A-Za-z0-9_.:-]*)"
)


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
        if first.startswith(("'", '"', "{", "[")):
            return True
        if first.lower() in ("basic", "bearer") and words["second"] and not words["third"]:
            return True
        # Natural-language clauses are not configuration values. Bare atomic
        # values remain a supported assignment spelling; this is not a parser.
        return words["second"] is None
    if (match["operator"] == "=" and any(c in match["spacing"] for c in "\r\n")
            and SETEXT_TAIL.match(text, match.end())):
        return False
    return True


def format_violation(text, sensitive_pattern=DEFAULT_SENSITIVE_KEY):
    """Return a static failure code; never include external text in diagnostics.

    Only explicit markup and sensitive assignments are classified. Ordinary
    unmarked prose is not parsed as a programming language. Callers supply the
    existing confidentiality policy's sensitive-key regex when they have one;
    legacy shell adapters use the default pattern above.
    """
    sensitive_pattern = re.compile(sensitive_pattern)
    fence = None
    prose = []
    offset = 0
    for line in text.splitlines(keepends=True):
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
                return ERROR_CODE
            fence = marker[1]
            prose.append("\0")
            continue
        # Container/indented fences are outside this contract. Delimiter escapes
        # do not opt code examples back into inline syntax.
        if re.search(r"`{3,}|~{3,}", body):
            return ERROR_CODE
        markers = list(TICKS.finditer(body))
        if len(markers) % 2:
            return ERROR_CODE
        cursor = 0
        for opening, closing in zip(markers[::2], markers[1::2]):
            if opening[0] != closing[0]:
                return ERROR_CODE
            reference = body[opening.end():closing.start()]
            if not REFERENCE.fullmatch(reference):
                return ERROR_CODE
            # Formatting only the key does not make an unfenced assignment safe.
            following = ASSIGNMENT_TAIL.match(text, line_start + closing.end())
            path_reference = any(char in reference for char in "/\\")
            qualified_colon = following and following["operator"] == ":" and any(
                char in reference for char in ".:")
            if (sensitive_pattern.search(reference) and following and not path_reference
                    and not qualified_colon and is_assignment(text, following)):
                return ERROR_CODE
            prose.append(body[cursor:opening.start()])
            prose.append("\0")
            cursor = closing.end()
        prose.append(body[cursor:] + "\n")
    if fence is not None:
        return ERROR_CODE
    assignment = re.compile(
        sensitive_pattern.pattern + r"""(?:\\?["'])?""" + ASSIGNMENT_TAIL.pattern,
        sensitive_pattern.flags)
    prose_text = "".join(prose)
    for match in assignment.finditer(prose_text):
        key = prose_text[match.start():match.start("spacing")]
        quoted_key = key.endswith(("'", '"'))
        if not quoted_key:
            if match.start() and prose_text[match.start() - 1] in "/\\.":
                continue
            if match["operator"] == ":" and any(char in key for char in ".:"):
                continue  # Unquoted path:line citations are not setting keys.
        if is_assignment(prose_text, match, quoted_key):
            return ERROR_CODE
    return None


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
