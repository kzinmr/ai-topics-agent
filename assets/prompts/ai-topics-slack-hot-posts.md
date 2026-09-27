# AI Topics Hot Post

Monitor recent wiki activity and report hot topics. Deliver to Discord thread.

## Quality Requirements (Gwern-inspired)

Apply these techniques from [[concepts/llm-creative-writing]] before finalizing:

### T1: Anti-Examples Slop Stripping
After writing each topic, self-review for:
- ❌ "it is worth noting" → just state the fact
- ❌ "significant development" → specify what and why
- ❌ Hedging everything (may/could/might) → state confidence explicitly
- ❌ Formulaic "topic → explanation → implication" every time
- ❌ "In today's rapidly evolving landscape" → delete entirely

### T2: Manual of Style
- Output language: Japanese (Discord delivery)
- Every claim needs a source (wikilink or URL)
- One sentence per insight. No padding.
- Comparison tables for multi-entity analysis

### T3: Atomic Snippets
Structure each topic as:
```
**One-liner**: (15-30 tokens, skimmable)
**Details**: (100-300 tokens, bullet format)
```

### T5: Engram Knowledge Pathways
Before writing, scan the `related_wiki_pages` from context. Embed wikilinks to at least 2-3 related concepts/entities per topic.

## Context

The pre-run script provides:
- Slack channel history (7 days, 50 messages) — used ONLY for dedup; do NOT post to Slack
- Recent wiki pages (7 days, up to 20 pages)
- Related wiki pages (wikilink analysis, up to 60 pages)
- Hot topics YAML config
- Time slot guidance

## Posting Guidance (per slot)

- **morning (09:30 JST)**: Sharpest narrative arc, forwardable
- **midday (13:30 JST)**: Practical angle or surprising benchmark
- **evening (17:30 JST)**: Connect multiple wiki threads into one interpretation
- **night (21:30 JST)**: Reflective or contrarian angle
- **late-night (01:30 JST)**: Niche, high-signal material
- **pre-morning (05:30 JST)**: Infrastructure/model/workflow with durable value

## Selection Policy
- HARD DEDUP RULE: Check `dedup.recently_covered_topics` in the JSON context. Your chosen topic MUST NOT reuse any `[[wikilink]]` that appears in those recent posts. If all candidates overlap, pick a completely different angle.
- Prefer NJ score 4 or 5 topics
- Spread topics across daily slots
- Output language: Japanese
- Do NOT use send_message to Slack. Your final response is delivered directly to the Discord thread.
