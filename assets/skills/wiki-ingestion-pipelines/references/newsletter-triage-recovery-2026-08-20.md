# Newsletter Wiki Ingest 2026-08-20 — Recovery Run

Session: newsletter-wiki-ingest run 2026-08-20, checkpoint 20260820T101038Z (2 newsletters: AINews/swyx Substack + beehiiv uid=526). Pre-run script reported `failed to parse JSON response from newsletter-triage output` (output `~/.hermes/cron/output/4e8b0d92c6a1/2026-08-20_10-41-27.md`).

## Outcome

Takes=1 (enriched `concepts/glm-5-3.md`), reference=1 (beehiiv "OpenAI Hits the Brakes on Itself" — all 20 links unresolvable, no wiki change), skip=2 (UI noise). Commit `3be32389`, pushed to main.

## Recovery details

Use the runner-provided profile HOME and canonical `~/wiki`. Do not infer alternate runtime paths.

## Lessons

- Checkpoint-first recovery worked exactly as the skill prescribes; the parse failure was response-rendering only.
- Targeted `git add` was essential: 6 sibling entity-page modifications stayed out of the commit.
- pull-rebase failure + successful push is a benign end state in the parallel pipeline window — do not stash/commit sibling work.
