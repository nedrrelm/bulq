#!/usr/bin/env python3
"""Block Bash commands that mutate docs/backlog.md or docs/devlog.md.

Reads a Claude Code PreToolUse JSON payload from stdin. Looks for common
mutation patterns (redirection, sed -i, mv, rm, cp, tee, truncate) targeting
the protected files. Reads (cat, grep, head, tail) and janus CLI invocations
are allowed.

Best-effort regex matching; pathological shell quoting can sneak through.
That's acceptable because agents aren't adversarial.
"""

from __future__ import annotations

import json
import re
import sys

PROTECTED = r"docs/(?:backlog|devlog)\.md"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf">>?\s*(?:[^\s|;&]*?/)?{PROTECTED}\b"), "shell redirection"),
    (re.compile(rf"\bsed\s+[^|;&]*?-i\b[^|;&]*?{PROTECTED}"), "sed -i"),
    (re.compile(rf"\bsed\s+[^|;&]*?--in-place\b[^|;&]*?{PROTECTED}"), "sed --in-place"),
    (re.compile(rf"\bawk\s+[^|;&]*?-i\b[^|;&]*?{PROTECTED}"), "awk -i"),
    (re.compile(rf"\bmv\s+[^|;&]*?{PROTECTED}"), "mv"),
    (re.compile(rf"\brm\s+[^|;&]*?{PROTECTED}"), "rm"),
    (re.compile(rf"\bcp\s+[^|;&]*?{PROTECTED}"), "cp"),
    (re.compile(rf"\btee\s+[^|;&]*?{PROTECTED}"), "tee"),
    (re.compile(rf"\btruncate\s+[^|;&]*?{PROTECTED}"), "truncate"),
]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return 0

    for pattern, label in PATTERNS:
        if pattern.search(cmd):
            sys.stderr.write(
                f"Bash mutation of docs/backlog.md or docs/devlog.md is blocked "
                f"(matched: {label}).\n"
                "Use the janus CLI for mutations:\n"
                "  janus add / mark / rm / edit / complete\n"
                "Reads via cat/grep/head/tail are fine; janus invocations are fine.\n"
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
