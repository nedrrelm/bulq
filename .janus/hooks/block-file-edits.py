#!/usr/bin/env python3
"""Block Edit/Write/NotebookEdit on docs/backlog.md and docs/devlog.md.

Reads a Claude Code PreToolUse JSON payload from stdin. Exits with code 2 to
block the tool call when the targeted path is one of the protected files.
"""

from __future__ import annotations

import json
import os
import sys

PROTECTED_BASENAMES = ("backlog.md", "devlog.md")


def is_protected(path: str) -> bool:
    if not path:
        return False
    normalized = os.path.normpath(path)
    parts = normalized.split(os.sep)
    return len(parts) >= 2 and parts[-2] == "docs" and parts[-1] in PROTECTED_BASENAMES


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""

    if is_protected(path):
        sys.stderr.write(
            "Direct edits to docs/backlog.md and docs/devlog.md are blocked.\n"
            "Use the janus CLI instead:\n"
            "  janus add / mark / rm / edit / complete   (mutate)\n"
            "  janus list / show / search                 (read)\n"
            "See the janus-backlog skill for details.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
