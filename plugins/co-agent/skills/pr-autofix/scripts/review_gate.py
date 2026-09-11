#!/usr/bin/env python3
"""Deterministic review-format and coverage gate; never judge or vote on findings."""
import argparse
import json
import re
from pathlib import Path

SEVERITIES = ("CRITICAL", "MAJOR", "MINOR", "INFO")
EMPTY_MARKERS = ("None", "None.", "없음", "없음.")


def decision(status, reason):
    return {"status": status, "reason": reason}


def visible_lines(text):
    """Ignore fenced/indented code, block quotes and HTML comments."""
    lines, fence, comment, quote = [], None, False, False
    for raw in text.splitlines():
        # Existing opaque blocks own their contents: a fence cannot open an HTML
        # comment, and a comment cannot open a fence or a block quote.
        if fence:
            match = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", raw)
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if comment:
            if "-->" not in raw:
                continue
            raw, comment = raw.split("-->", 1)[1], False
        if raw.lstrip().startswith(">"):
            quote = True
            continue
        if quote:
            if not raw.strip() or re.match(r" {0,3}(?:#{1,6} |[-+*] |\d+[.)] |`{3}|~{3})", raw):
                quote = False
            else:
                continue
        match = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", raw)
        if match and (match[1][0] != "`" or "`" not in match[2]):
            fence = match[1]
            continue
        if raw.startswith(("    ", "\t")):
            continue
        while "<!--" in raw:
            before, after = raw.split("<!--", 1)
            if "-->" not in after:
                raw, comment = before, True
                break
            raw = before + after.split("-->", 1)[1]
        lines.append(raw.strip())
    return lines, bool(fence or comment)


def markdown_review(text):
    lines, unclosed = visible_lines(text)
    issues, section, category, counts, ignored = 0, "", None, {}, False
    errors = ["Unclosed quoted/code content"] if unclosed else []
    verdicts = []
    for line in lines:
        verdict = re.fullmatch(r"VERDICT: (PASS|FAIL)(?:[ \t].*)?", line)
        if verdict:
            verdicts.append(verdict[1])
        heading = re.fullmatch(r"(#{1,6})\s+(.+?)(?:\s+#+)?", line)
        if heading:
            level, title = len(heading[1]), heading[2].strip()
            if level <= 2:
                section, category, ignored = title.casefold(), None, False
                if section == "review error":
                    return decision("ERROR", "Chair reported an incomplete review")
                if section == "issues":
                    issues += 1
                    if level != 2:
                        errors.append("Issues must be a level-two heading")
            elif section == "issues" and level == 3:
                category = title.upper() if title.upper() in SEVERITIES else None
                ignored = title.casefold().startswith(("dismissed", "suggestions", "memory", "panel quality", "🧠"))
                if category:
                    if category in counts:
                        errors.append("Duplicate severity section")
                    counts.setdefault(category, [])
                elif not ignored:
                    errors.append("Unrecognized Issues subsection")
            elif section == "issues":
                errors.append("Unexpected heading inside Issues")
            continue
        if section == "issues" and category and line:
            counts[category].append(line)
        elif section == "issues" and line and not ignored:
            errors.append("Unclassified text inside Issues")
    # An explicit active finding cannot be excused by PASS or malformed text elsewhere.
    for severity in SEVERITIES:
        for line in counts.get(severity, []):
            item = re.fullmatch(r"(?:[-+*]|\d+[.)])\s+(\S.*)", line)
            if item:
                if item[1] in EMPTY_MARKERS:
                    errors.append("Write empty markers without a list marker")
                elif severity in SEVERITIES[:2]:
                    return decision("BLOCKED", f"Active {severity} finding in final Issues")
    if len(verdicts) != 1:
        return decision("ERROR", "Review must contain one unquoted VERDICT: PASS or FAIL")
    if verdicts[0] == "FAIL":
        return decision("BLOCKED", "Chair returned VERDICT: FAIL")
    if issues != 1 or not set(SEVERITIES[:3]) <= counts.keys():
        errors.append("Missing or duplicate canonical Issues/severity sections")
    for body in counts.values():
        if not (len(body) == 1 and body[0] in EMPTY_MARKERS) and not (
            body and re.match(r"(?:[-+*]|\d+[.)])\s+\S", body[0])
        ):
            errors.append("Severity section must contain findings or one standalone empty marker")
    if errors:
        return decision("ERROR", errors[0])
    return decision("PASSED", "Explicit Issues contain no active CRITICAL or MAJOR findings")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON member")
        value[key] = item
    return value


def json_review(text):
    report = json.loads(text, object_pairs_hook=unique_object)
    nonempty = lambda value: isinstance(value, str) and bool(value.strip())
    if (not isinstance(report, dict) or set(report) - {"status", "summary", "findings", "dismissed"}
            or report.get("status") not in ("PASSED", "BLOCKED", "ERROR")
            or not nonempty(report.get("summary")) or not isinstance(report.get("findings"), list)
            or not isinstance(report.get("dismissed", []), list)):
        raise ValueError("Invalid review schema")
    for name in ("findings", "dismissed"):
        required = {"severity", "file", "line", "message"} | ({"reason"} if name == "dismissed" else set())
        for finding in report.get(name, []):
            if (not isinstance(finding, dict) or set(finding) != required
                    or finding["severity"] not in SEVERITIES
                    or not all(nonempty(finding[key]) for key in required - {"line"})
                    or (finding["line"] is not None and not (
                        type(finding["line"]) is int and 0 < finding["line"] <= 9007199254740991))):
                raise ValueError("Invalid finding schema")
    if report["status"] == "ERROR":
        return decision("ERROR", "Reviewer reported an incomplete review")
    if report["status"] == "BLOCKED" or any(f["severity"] in SEVERITIES[:2] for f in report["findings"]):
        return decision("BLOCKED", "Active blocking findings or reviewer BLOCKED status")
    return decision("PASSED", "No active blocking findings")


def coverage_error(work, truncated):
    if truncated or any((work / name).exists() for name in (
        "kiro-diff-truncated.flag", "panel-cell-truncated.flag", "coverage-severe.flag",
    )):
        return "Required review input or coverage is incomplete"
    degraded = work / "degraded-models.txt"
    if degraded.exists() and degraded.read_text().strip():
        return "A configured reviewer did not complete"
    expected = (work / "expected.txt").read_text().splitlines()
    responded = (work / "responded.txt").read_text().splitlines()
    if (not expected or len(set(expected)) != len(expected) or sorted(expected) != sorted(responded)
            or not all(re.fullmatch(r"[a-z0-9-]+/[A-Za-z0-9_.-]+", cell) for cell in expected)):
        return "Not every configured review cell completed"
    for cell in expected:
        if not (work / "slot" / (cell.replace("/", "-") + ".md")).read_text().strip():
            return "A required review cell has no usable output"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("format", choices=("markdown", "json"))
    parser.add_argument("report", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--chair-error", choices=("0", "1"), default="0")
    parser.add_argument("--l1-failed", choices=("0", "1"), default="0")
    parser.add_argument("--diff-truncated", choices=("0", "1"), default="0")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--status-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.chair_error == "1":
            result = decision("ERROR", "Chair CLI failed or produced no usable review")
        elif args.l1_failed == "1":
            validated = args.work_dir and (args.work_dir / "l1-validators-started").is_file()
            result = decision("BLOCKED" if validated else "ERROR",
                              "L1 validation failed" if validated else "L1 infrastructure failed")
        else:
            data = args.report.read_bytes()
            if not data.strip() or len(data) > 50000:
                raise ValueError("Missing, empty or oversized review")
            result = (markdown_review if args.format == "markdown" else json_review)(data.decode("utf-8"))
            if args.work_dir and result["status"] == "PASSED":
                error = coverage_error(args.work_dir, args.diff_truncated == "1")
                if error:
                    result = decision("ERROR", error)
    except (OSError, ValueError, TypeError, KeyError):
        result = decision("ERROR", "Review or required coverage evidence is missing or malformed")
    if args.github_output:
        status = {"PASSED": "pass", "BLOCKED": "fail", "ERROR": "error"}[result["status"]]
        with args.github_output.open("a") as output:
            output.write(f"result={status}\nreason={result['reason']}\n")
    print(result["status"] if args.status_only else json.dumps(result))


if __name__ == "__main__":
    main()
