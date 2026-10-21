# Agent-facing documentation conventions (primary sources)

Ticket: what do primary sources recommend for documenting a Python library so coding agents use it correctly? Researched 2026-10-21. Quotes are verbatim from the fetched pages; where a source is silent this is stated.

Sources:
- [CC-MEM] https://code.claude.com/docs/en/memory
- [CC-BP] https://code.claude.com/docs/en/best-practices
- [CC-SK] https://code.claude.com/docs/en/skills
- [SK-BP] https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- [AGENTS] https://agents.md
- [LLMS] https://llmstxt.org
- [CTX] https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

## 1. Entry-point file role and size limits

- Role: CLAUDE.md gives "persistent context it can't infer from code alone": Bash commands, code style, workflow rules [CC-BP]. Claude reads it at the start of every session and treats it "as context, not enforced configuration"; enforcement belongs in hooks [CC-MEM].
- AGENTS.md is "a dedicated, predictable place to provide the context and instructions to help AI coding agents work on your project"; suggested sections: project overview, build and test commands, code style, testing instructions, security considerations; "anything you'd tell a new teammate" [AGENTS]. No required fields: "just standard Markdown" [AGENTS].
- Size: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." [CC-MEM]. The AGENTS.md site gives no size guidance [AGENTS]. llms.txt: the file "stays small enough to fit in context", with details behind links [LLMS].
- Include / exclude table [CC-BP]:
  - Include: commands Claude can't guess; style rules differing from defaults; test runners; repo etiquette; project-specific architectural decisions; env quirks; non-obvious gotchas.
  - Exclude: "Anything Claude can figure out by reading code"; standard language conventions; "Detailed API documentation (link to docs instead)"; "Information that changes frequently"; "Long explanations or tutorials"; "File-by-file descriptions of the codebase".
- Pruning test: "For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!" [CC-BP]
- Context altitude: instructions should be "specific enough to guide behavior effectively, yet flexible enough to provide the model with strong heuristics"; "the minimal set of information that fully outlines your expected behavior" where "minimal does not necessarily mean short" [CTX].
- Skills: description is the discovery text; combined description + when_to_use is truncated at 1,536 chars in the listing [CC-SK]; the platform spec caps description at 1,024 chars, third person, covering "what the Skill does and when to use it" [SK-BP].
- Interop: Claude Code reads AGENTS.md only when no CLAUDE.md exists in or above the working dir; if both exist, "Your CLAUDE.md files only". A CLAUDE.md can import AGENTS.md. [CC-MEM] The AGENTS.md site advises renaming to AGENTS.md and symlinking old names (`mv AGENT.md AGENTS.md && ln -s AGENTS.md AGENT.md`) [AGENTS].

## 2. Progressive disclosure and linking

- Principle: agents should "incrementally discover relevant context through exploration" and keep "lightweight identifiers (file paths, stored queries, web links, etc.)"; CLAUDE.md files "are naively dropped into context up front" [CTX].
- CLAUDE.md is for broadly applicable content; "For domain knowledge or workflows that are only relevant sometimes, use skills instead. Claude loads them on demand" [CC-BP].
- Imports: `@path/to/import`; "Imported files are expanded and loaded into context at launch"; max depth four hops; imports "help you organize a long file but don't reduce its context cost" [CC-MEM]. Code spans/fences are not parsed as imports; backticks keep `@path` literal [CC-MEM].
- Real lazy loading in Claude Code: subdirectory CLAUDE.md/AGENTS.md "load on demand" when Claude works there; `.claude/rules/*.md` with `paths:` frontmatter "only load into context when Claude works with matching files" [CC-MEM]. AGENTS.md: "Agents automatically read the nearest file in the directory tree, so the closest one takes precedence"; "Large monorepo? Use nested AGENTS.md files for subprojects." [AGENTS]
- Skills: SKILL.md "loads only when it's used, so long reference material costs almost nothing until you need it" [CC-SK]; keep SKILL.md "under 500 lines. Move detailed reference material to separate files" [CC-SK, SK-BP]; reference supporting files from SKILL.md "so Claude knows what each file contains and when to load it" [CC-SK].
- Link shape [SK-BP]: keep references one level deep from SKILL.md (with nested references "Claude might use commands like `head -100` to preview content"); reference files over 100 lines get a table of contents at the top; name files descriptively (`form_validation_rules.md`, not `doc2.md`); organise by domain (`reference/finance.md`); say whether Claude should execute or read a script.
- llms.txt layout: H1 project name (the only required part), blockquote summary, optional prose, H2 sections of markdown link lists (`- [name](url): notes`); an "Optional" H2 marks secondary links that can be skipped; recommends clean `.md` versions of pages [LLMS].
- Maintainer-only notes: block-level HTML comments in CLAUDE.md are stripped before injection, so they cost no context [CC-MEM].

## 3. Generated reference vs hand-written recipes

- Keep "Detailed API documentation (link to docs instead)" and "File-by-file descriptions of the codebase" out of the entry file [CC-BP]. Large reference material belongs in on-demand files [CC-SK, SK-BP]: "Bundle comprehensive resources: Include complete API docs, extensive examples, large datasets; no context penalty until accessed" [SK-BP].
- Examples beat prose: "Examples convey the desired style and level of detail to Claude more clearly than descriptions alone" (input/output pairs); templates strict or flexible depending on need [SK-BP]. Provide a default, not many options (one recommended tool plus an escape hatch) [SK-BP].
- Prefer scripts for deterministic operations; pre-made scripts are "more reliable than generated code" and save tokens, since only output consumes context [SK-BP].
- Only add what Claude lacks: "Does Claude really need this explanation?" [SK-BP]. Use consistent terminology: "Choose one term and use it throughout" [SK-BP].
- Set freedom per task: exact commands for fragile steps, heuristics for open ones [SK-BP].
- Sources do not state a generated-vs-handwritten split for library APIs. llms.txt only notes that doc platforms can generate llms.txt / markdown page versions automatically (Mintlify, Yoast, Wix) [LLMS]. No source examined prescribes a docstring-to-Markdown generator.

## 4. Keeping docs in sync with code

- "Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, and test changes by observing whether Claude's behavior actually shifts." `/doctor` proposes cuts for content derivable from the codebase [CC-BP]. Check it into git [CC-BP].
- Contradictions: "if two instructions contradict each other, Claude may pick one arbitrarily. Review your CLAUDE.md files, nested CLAUDE.md files ... and .claude/rules/ periodically to remove outdated or conflicting instructions"; `/doctor prompt-audit` audits CLAUDE.md, AGENTS.md, rules, skills [CC-MEM].
- Avoid drift-prone content: exclude "Information that changes frequently" [CC-BP]; no time-sensitive info, use an "old patterns" section [SK-BP]. AGENTS.md: "Treat AGENTS.md as living documentation"; it can be updated later [AGENTS].
- Evaluation-driven: "Create evaluations BEFORE writing extensive documentation"; at least three evaluations; test with Haiku, Sonnet, Opus; observe where a fresh instance misses or ignores files, then revise [SK-BP].
- Verification over prose: give Claude "a check it can run: tests, a build, a screenshot" [CC-BP]; validator loops (run validator, fix, repeat) [SK-BP]. AGENTS.md: tests run automatically "if you list them" [AGENTS].
- Sources describe no CI check that diffs docs against code. llms.txt says nothing on sync beyond plugins that "generate and maintain" the file [LLMS].

## Implications for dexpigen

1. CLAUDE.md (currently a short project map, within the 200-line target) fits the stated role; keep it to commands, rules, and pointers, and push domain facts out of it.
2. The ~100-class API counts as "detailed API documentation": per [CC-BP] link it rather than inline it. CONTEXT.md (glossary) is a candidate on-demand file.
3. Use one-level-deep links from the entry file to topic files (each with a TOC if over 100 lines), descriptive filenames, and a "when to read this" note per link; `@` imports do not save context.
4. Recipes should be concrete input/output examples with a single default path (e.g. examples/C01/build.py) plus runnable validation (examples/validate_dexpi.py), which the sources rate above prose.
5. Sources are silent on generating reference from code and on doc-vs-code CI; sync guidance reduces to: keep frequently changing facts out of prose, prune periodically, run the audit, and verify with executable checks/evaluations. Path-scoped rules or nested CLAUDE.md/AGENTS.md can scope per-package notes (e.g. serialization vs model).
