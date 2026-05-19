---
name: janus
description: Use when reading or mutating per-project markdown backlogs managed by Janus. Triggers in any project that has docs/backlog.md. Covers the janus CLI and the file format rules.
---

# Janus backlog skill

## What this skill is for

Janus is a per-project backlog tool. Each project has `docs/backlog.md` (open work) and optionally `docs/devlog.md` (completed work). Both are plain markdown with a strict format. The `janus` CLI is the **only** sanctioned way to mutate them — direct edits via Edit/Write or shell redirection are hook-blocked.

## Files

- `docs/backlog.md` — open items, plus `## Notes` and `## Future Work` sections.
- `docs/devlog.md` — completed items (auto-created on first `janus complete`).
- `backlog-format.md` — full format specification (present in the Janus repo; not always shipped to indexed projects).

## Schema cheat sheet

Each backlog item is an H3 heading followed by a fenced YAML block, then a freeform body:

````markdown
### [<slug>-NNNN] <Title>

```yaml
type: feature | bug | refactor | exploration
status: open | doing | blocked | done | wontfix
areas: [backend, frontend, infrastructure, db, docs, app]   # one or more
priority: low | medium | high   # optional
created: YYYY-MM-DD
updated: YYYY-MM-DD
depends_on: [<id>, ...]   # optional
tags: [tag1, tag2]        # optional
```

Body markdown.

#### Acceptance
- [ ] criterion
````

Devlog items add a required `completed: YYYY-MM-DD` field. The `slug` is derived from the H1 title of the file (e.g. `# Janus Backlog` → `janus`). IDs are globally unique across all Janus projects.

## CLI reference

### Read

- `janus list [--type T] [--status S] [--area A] [--tag T]` — Rich table of items: ID, status, type, areas, priority, title. No body. Filters take comma-separated values: `--status open,doing`.
- `janus show <id>` — full detail: heading, raw YAML, and body.
- `janus search <query>` — case-insensitive substring across heading, YAML, and body.
- `janus notes [--set "..."]` — print the Notes section body, or replace it with `--set`.
- `janus future-work [--set "..."]` — print the Future Work section body, or replace it with `--set`.

### Mutate

- `janus add --title "..." --type <t> --areas <a1,a2> [--priority <p>] [--tags t1,t2] [--depends-on id1,id2] [--body "..."] [--status <s>]`
  Creates the next available ID. `--status done` is rejected; new items can't start as done.
- `janus mark <id> <status>` — change status. Rejects `done` — use `complete` instead. Bumps `updated`.
- `janus edit <id> [--title "..."] [--type T] [--areas a1,a2] [--priority P] [--tags t1,t2] [--depends-on id1,id2] [--body "..."] [--status S]`
  Two modes:
  - **With flags** (preferred for agents) — patches only the supplied fields in place, no editor. `--status done` is rejected; use `complete` instead.
  - **Without flags** — opens the item block in `$EDITOR`; re-validates on save. File is left untouched if the result is invalid. **Never call this form as an agent** — it opens an interactive terminal and will hang. Always supply at least one flag.
- `janus complete <id>` — sets `status: done`, adds `completed: <today>`, moves the item from `docs/backlog.md` to `docs/devlog.md`. Creates the devlog file on first use.
- `janus rm <id>` — removes the item from the backlog. No confirmation. Doesn't move to devlog.

### Maintenance

- `janus validate [path ...]` — validate one or more backlog/devlog files. Defaults to `docs/backlog.md`. Exits 0 on success; non-zero with rule-numbered errors on failure. Auto-detects backlog vs devlog from the H1 title (`Backlog` / `Devlog` suffix).

## Canonical workflow

1. **Read first.** If the user names a specific item, go straight to `janus show <id>`. Otherwise use `janus list` for an overview or `janus search <query>` to search body text.
2. **Pick the right verb for the mutation**:
   - new item → `janus add`
   - status change (anything except `done`) → `janus mark <id> <status>`
   - patch specific fields (title, type, areas, priority, tags, body, status) → `janus edit <id> --field value`
   - mark something done → `janus complete <id>`
   - drop an item without devlog entry → `janus rm <id>`
3. Every mutation re-validates before writing. If validation fails, the file is left untouched — fix the input and try again.
4. **Never** use Edit, Write, or NotebookEdit on `docs/backlog.md` or `docs/devlog.md`. **Never** use Bash redirection (`>`, `>>`), `sed -i`, `awk -i`, `mv`, `rm`, `cp`, `tee`, or `truncate` against them. These are blocked by PreToolUse hooks with a clear error message.

## Common error patterns

Validator output looks like `docs/backlog.md:17: rule 4: item 'janus-0002' has no YAML metadata block`. The rule number maps to `backlog-format.md` §6:

- **Rule 1** — H1 / section structure (exactly one H1; for backlogs the three H2s must be present in order).
- **Rule 2** — section presence/order. Devlogs only allow `## Items`.
- **Rule 3** — H3 heading shape. Use `### [<slug>-NNNN] <title>`.
- **Rule 4** — YAML fence missing right after the H3.
- **Rule 5** — YAML field violation: wrong enum value, missing required field, wrong type, unknown field (`extra="forbid"`).
- **Rule 6** — duplicate ID within the file.
- **Rule 7** — `depends_on` references an ID that doesn't exist in this file or its sibling devlog/backlog.
- **Rule 8** — ID slug doesn't match the project slug derived from the H1 title.

When you hit one, read the line number and rule, fix the input, and retry the CLI command — don't try to edit around the validator.

## Related skills

- **refine-notes** — use after `janus init` absorbs an existing informal backlog into `## Notes`. Converts unstructured notes into proper backlog items via `janus add`.
