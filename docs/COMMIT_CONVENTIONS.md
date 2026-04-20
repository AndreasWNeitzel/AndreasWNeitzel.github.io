# COMMIT_CONVENTIONS.md — Git Commit Message Format

All commits in this repository follow these conventions. This keeps the git history readable and makes debugging easier.

## Format

```
<imperative verb> <what changed>

<optional body explaining why, wrapped at 72 chars>
```

- **Subject line:** imperative mood, ≤72 characters, no trailing period
- **Body (optional):** blank line after subject, then free prose explaining why
- **One logical change per commit** — do not batch unrelated changes

## Imperative mood examples

Good (imperative, describes what the commit _does_):

- `Configure _config.yml with Neitzel identity`
- `Add three publications to papers.bib`
- `Hide Blog and News from navigation`
- `Replace CV page with simple PDF link`
- `Update About page with canonical prose`

Bad:

- `Configured config file` (past tense)
- `Configuring config` (gerund)
- `config update` (not a sentence)
- `fixed stuff` (vague)

## Grouping

Group commits by logical scope, not by file. Examples:

**Good:** One commit per concern

- `Configure site identity and social links`
- `Populate publications from BibTeX`
- `Hide unused pages (Blog, News, Teaching, Projects)`
- `Replace About page content`

**Bad:** One commit for everything

- `Initial Neitzel site setup` (too broad — hides what changed)

**Bad:** One commit per file when files are related

- `Edit blog.md`, `Edit news.md`, `Edit teaching.md`, `Edit projects.md` (should be one commit: "Hide unused pages")

## When in doubt

If unsure whether two changes should be one commit or two: ask "does the commit message describe one thing or two things joined by 'and'?" If two things, split.

## What not to commit

Never commit:

- Draft content that hasn't been reviewed
- Files in `_site/` or `.jekyll-cache/` (these are build outputs)
- Personal files (`.DS_Store`, editor backups, etc.)
- API keys, tokens, or credentials
- Large binary files that aren't site assets
