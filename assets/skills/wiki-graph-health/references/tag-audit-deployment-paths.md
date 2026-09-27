# Tag Audit — Deployment-Specific Script Paths

This deployment's tag audit scripts live at non-default locations. The canonical skill directory path `~/.hermes/skills/wiki/wiki-graph-health/scripts/` **does not exist** in this environment — do not attempt to run scripts there.

## Actual Script Locations

| Script | Path | Verified |
|--------|------|----------|
| `tag_audit.py` | `~/.hermes/scripts/tag_audit.py` | ✅ Exists, works |
| `tag_normalization.py` | `~/ai-topics/config/hermes/skills/_overrides/wiki-graph-health/scripts/tag_normalization.py` | ✅ Exists, works |
| Skill scripts dir | `~/.hermes/skills/wiki/wiki-graph-health/scripts/` | ❌ Does not exist |

## Run Sequence

```bash
cd ~/ai-topics

# Phase 1: Audit
python3 ~/.hermes/scripts/tag_audit.py
python3 ~/.hermes/scripts/tag_audit.py --suggest-additions --min-usage 2

# Phase 2: Normalize (dry-run first, then apply)
python3 ~/ai-topics/config/hermes/skills/_overrides/wiki-graph-health/scripts/tag_normalization.py --dry-run
python3 ~/ai-topics/config/hermes/skills/_overrides/wiki-graph-health/scripts/tag_normalization.py

# Phase 3: Verify
python3 ~/.hermes/scripts/tag_audit.py

# Phase 4: Commit
git add wiki/
git commit --no-verify -m "wiki: weekly tag audit auto-fix — N violations resolved, N pages normalized"
git push
```

## Pitfalls Confirmed in This Deployment

1. **Script not in skill directory**: The canonical SKILL.md path `~/.hermes/skills/wiki/wiki-graph-health/scripts/` does not exist. Fall back to `~/.hermes/scripts/` for `tag_audit.py` and the `_overrides/` path for `tag_normalization.py`.
2. **Cron pre-run block**: The cron job `tag-audit-weekly` cannot use `script:` to pre-run `tag_audit.py` because the script resolves outside the restricted `~/.hermes/scripts/` directory. Run it as the first step within the agent session instead.
3. **tag_normalization.py from repo overrides**: The normalization script lives under `config/hermes/skills/_overrides/` — do NOT try to run it from `~/.hermes/scripts/` (it doesn't exist there) or from the default skill dir.
