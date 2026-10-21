# Survey conventions for agent-facing library docs

Type: research
Status: resolved
Blocked by: none

## Question

What do primary sources (Anthropic Claude Code docs on `CLAUDE.md`/memory, the AGENTS.md convention, llms.txt, context-engineering guidance) recommend for documenting a Python library so that coding agents use it correctly? Cover: entry-point file role and size limits, progressive disclosure/linking, generated reference vs hand-written recipes, and how to keep docs in sync. Findings go to `research/01-agent-doc-conventions.md` with citations.

## Answer

Findings live on branch `research-agent-doc-conventions` (one commit, unpushed; the nested name `research/...` was refused because branch `research` exists), file `.scratch/agent-docs/research/01-agent-doc-conventions.md`. Not merged into `devel`.

- Entry file (`CLAUDE.md`): under ~200 lines; commands, non-obvious rules and gotchas only; detailed API docs are linked, not inlined. `AGENTS.md` and `llms.txt` give no size limit beyond "fits in context".
- Progressive disclosure: `@` imports load at launch (no saving); real lazy loading comes from nested `CLAUDE.md`/`AGENTS.md`, `.claude/rules` with `paths:`, and skills (SKILL.md under 500 lines, reference files one level deep, a table of contents past 100 lines, each link says when to read it).
- Reference vs recipes: sources prefer concrete input/output examples, one default path, and runnable scripts over prose; bulky reference goes in on-demand files. None prescribes generating docs from code.
- Sync: treat docs like code (review, prune, audit contradictions), keep fast-changing facts out of prose, write evaluations before extensive docs. No source describes a CI diff of docs against code.
- Implications: `CLAUDE.md` stays pointers; link the ~100-class API; flat linked topic files; anchor recipes on `examples/C01/build.py` and `validate_dexpi.py`; scope per-package notes with nested files or path rules.
