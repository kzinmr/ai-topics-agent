# Daily Skeleton Enrichment

You are an AI wiki maintenance agent. Your task is to enrich "skeleton" entity pages — minimal pages with just frontmatter and a brief description — into comprehensive, well-researched profiles.

## ⚠️ CRITICAL: Git History Enrichment Pattern (MANDATORY)

Before enriching ANY page, check if a richer version exists in git history:

```bash
# Find the richest historical version
for commit in $(git log --format=%H -- 'wiki/entities/<slug>.md' 2>/dev/null | head -10); do
    lines=$(git show "$commit:wiki/entities/<slug>.md" 2>/dev/null | wc -l)
    echo "$commit $lines lines"
done | sort -rn -k2 | head -3
```

If a richer version exists (more lines than current), restore it FIRST with `git show <commit>:<path>`, then enrich on top of that with `patch`. Do NOT start from scratch when git history has a better version.

## ⚠️ CRITICAL: Pre-Write Verification (MANDATORY)

Before ANY `write_file` to `wiki/entities/`:
1. Read the existing page with `read_file` first
2. If the page has >40 lines of content, use `patch` — NEVER `write_file`
3. Check git history for richer versions before starting enrichment

## Task

Find entity pages with `status: skeleton` in their frontmatter and enrich them to comprehensive quality. Target 8-12KB for the final enriched page, matching `antirez-com.md` or `simon-willison.md` depth.

## Workflow

1. Search for skeleton pages: `search_files(path="wiki/entities", pattern="status: skeleton")`
2. For each skeleton page:
   a. Read the existing content
   b. Check git history for a richer version (see above)
   c. If richer version exists, restore it and merge
   d. Research the person/entity via web search
   e. Enrich with `patch` — add sections for background, contributions, key ideas, notable works, related entities
   f. Remove `status: skeleton` from frontmatter
   g. Update `updated` date
3. Update index.md with any new cross-references
4. Commit and push changes

## Quality Standards

- Include bio, professional background, key contributions
- Link to related wiki entities and concepts with [[wikilinks]]
- Cite sources (blog URLs, X posts, articles)
- Add X/Twitter handle if known
- Include notable quotes if available
