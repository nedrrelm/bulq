---
name: refine-notes
description: Use when docs/backlog.md has unstructured content in ## Notes that needs to be converted into structured backlog items. Typically triggered after janus init absorbs an existing informal backlog.
---

# Refine Notes into Backlog Items

Use this skill when `docs/backlog.md` has unstructured content in `## Notes` that was
absorbed from an existing informal backlog during `janus init`.

## Workflow

1. **Read the Notes section**
   ```
   uv run janus notes
   ```

2. **Identify distinct actionable tasks, features, or bugs**
   Skip vague/aspirational notes, links, and context that isn't work to be done.

3. **For each actionable item, decide:**
   - `type`: `feature | bug | refactor | exploration`
   - `areas`: one or more of `backend frontend infrastructure db docs app`
   - `priority` (if inferable from the text): `low | medium | high`

4. **Create each item:**
   ```
   uv run janus add --title "..." --type <type> --areas <a1,a2> [--priority <p>] [--body "..."]
   ```
   One `janus add` per item. Use the original wording where possible. Include `--body` for any detail worth preserving. To add or replace body text after creation: `uv run janus edit <id> --body "..."`.

5. **Leave non-actionable content in Notes** — context, background, links, references.

6. **Clean up the Notes section.** Remove converted items; keep non-actionable context:
   ```
   uv run janus notes --set "remaining non-actionable content"
   ```
   To clear it entirely: `uv run janus notes --set ""`

7. **Verify:**
   ```
   uv run janus list
   uv run janus validate docs/backlog.md
   ```

## Guidelines

- One idea = one item; don't over-split
- Don't create items for things already done
- Preserve priority signals from the original text ("urgent", "critical", "nice to have")
- If the original phrasing is ambiguous, create the item and leave a clarifying note in its body
