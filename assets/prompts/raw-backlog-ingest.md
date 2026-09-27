# Raw Backlog Ingest — AI Topics Wiki

You are processing the raw article backlog for the AI Topics Wiki.

## ⚠️ CRITICAL: Pre-Write Verification (MANDATORY)

Before ANY `write_file` to `wiki/entities/` or `wiki/concepts/`:
1. Read the existing page with `read_file` first
2. If the page has >40 lines of content, you MUST use `patch` to add/update — NEVER `write_file`
3. Overwriting rich curated pages with skeletons is a data-loss incident

Real failure: Thariq Shihipar's 282-line page was overwritten with a 36-line skeleton (commit 8dea159). The pre-commit hook now blocks this, but you should prevent it at the source.

## Script output context

The script output above is from `raw_backlog_collect.py`, which selects a bounded batch of unprocessed raw articles from the backlog sorted by AI relevance hint. The batch size may vary for manual runs; process exactly the articles listed in the script output.

## Your task

For each article in the batch:

1. Read the article file to understand its content
2. Check wiki/index.md for existing related pages
3. If an entity or concept page already exists with substantial content (>40 lines), use `patch` to add the new article as a source and add relevant sections — do NOT overwrite
4. If no page exists, create one following SCHEMA.md conventions
5. Update index.md and log.md

## Workflow
1. Process every article listed in the script output
2. For each article: read → check existing pages → create or patch → update index/log
3. git add, commit, and push all changes in one batch
4. Report what was created/updated
