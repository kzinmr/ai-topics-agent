Incoming X bookmarks batch attached below. Use `~/ai-topics` as the canonical repo root for this job.

## ⚠️ CRITICAL: Pre-Write Verification (MANDATORY)

Before ANY `write_file` to `wiki/entities/` or `wiki/concepts/`:
1. Read the existing page with `read_file` first
2. If the page has >40 lines of content, you MUST use `patch` to add/update — NEVER `write_file`
3. Overwriting rich curated pages with skeletons is a data-loss incident

## Task

For each bookmark in the batch:
1. Extract the main topic, author, and any linked URLs
2. For linked articles: fetch full text and save to `~/wiki/raw/articles/` with proper filename
3. For X tweets/posts: extract the key insight and any linked content
4. Create or update wiki entity/concept pages following SCHEMA.md
5. Check existing pages BEFORE writing — use `patch` for pages >40 lines
6. Update index.md and log.md
7. Commit and push all changes

Follow the wiki-entity-enrichment-from-article skill for page creation and enrichment.
