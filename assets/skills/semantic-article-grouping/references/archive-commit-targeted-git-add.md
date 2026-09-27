# Archive Commit — Targeted git add + Symlink Path Check

Validated 2026-08-01 (blog-triage cron run, 20 decisions: 2 takes / 6 refs / 12 skips, 18 items archived).

## Why triage jobs must commit the archive file

Triage itself makes **no wiki page edits** — the downstream wiki-ingest job owns page changes. The
archive JSON under `wiki/raw/archived/triage/{pipeline}/` is the **only repo artifact triage produces**,
and it IS git-tracked (`git ls-files wiki/raw/archived/triage/blog/` shows the dated files + `archive_index.json`).
Leaving it uncommitted loses the skip/reference audit trail and the dedup index; future runs can re-archive
or double-commit.

## Targeted `git add` — never blanket `git add wiki/`

The ai-topics repo routinely carries **unrelated dirty files** at triage time: skill edits under
`config/hermes/skills/` (other agents' skill-library maintenance), config changes, in-flight commits from
sibling pipeline jobs. A blanket `git add wiki/` sweeps none of those (they're under `config/`), but a
blanket `git add -A` or `git add .` absolutely would — polluting the triage commit with a misleading message.

Correct pattern (verified):
```bash
cd ~/ai-topics
git add wiki/raw/archived/triage/blog/2026-08-01_20260801T101221Z.json
git commit -m "blog-triage: archive 18 skip/reference decisions (2026-08-01)"
git push
```
Use the pipeline name matching the run (`blog|newsletter|dreaming`). Then `git push` with output
piped to `cat` (avoids pager hang).

## Symlink path check — nested-looking `archive_path` is NOT a failure

`archive_triage.py` prints an `archive_path` that can look wrong:
> Historical host repair example retired. Use `ai-topics-agent doctor` and the migration runbook.Use the runner-provided profile HOME and canonical `~/wiki`. Do not infer alternate runtime paths.

> Historical host repair example retired. Use `ai-topics-agent doctor` and the migration runbook.

Then confirm the file is tracked in git (`git status --short` shows the new archive as untracked before
`git add`, and the commit contains exactly one file).

## Pitfall guardrails

- Do NOT commit the triage JSON itself (`~/.hermes/cron/data/{pipeline}/triage_latest.json`) — it lives
  outside the repo on purpose (pipeline state, not wiki content).
- If pre-commit hook blocks the commit (tag/index validation), the failure is in staged wiki content —
  check whether a prior `git add` staged more than the archive file. With the targeted add, this should
  not happen.
- The 18-item archive count in the commit message = number of skip+reference decisions (takes are excluded
  by `--keep-reference` and become wiki pages downstream).
