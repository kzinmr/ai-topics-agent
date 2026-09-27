# Cron HOME Path Mismatch Fix for blogwatcher-cli

## Problem

Use the runner-provided profile HOME and canonical `~/wiki`. Do not infer alternate runtime paths.

## Affected File

`~/.hermes/scripts/daily_inbox_collect.py` (canonical cron copy; NOT `~/.hermes/scripts/daily_inbox_collect.py` which is a different version)

## Exact Patch (2 changes)

### Change 1: DB path resolution (line ~26)

```python
# BEFORE:
_BW_HOME = Path.home() / ".blogwatcher"

# AFTER:
# Use PROFILE_ROOT instead of Path.home() because cron HOME may differ from the actual user home
_BW_HOME = PROFILE_ROOT / ".blogwatcher"
```

### Change 2: Subprocess environment in run_blogwatcher_scan() (line ~52)

```python
# BEFORE:
env = {**os.environ, "BLOGWATCHER_YES": "1"}

# AFTER:
env = {**os.environ, "BLOGWATCHER_YES": "1", "HOME": str(PROFILE_ROOT)}
```

## Verification

```bash
# Should show 132 blogs (not "No blogs tracked yet")
HOME=~ blogwatcher-cli blogs | head -5

# Run the full ingest
cd ~ && HOME=~ ~/.hermes/venv/bin/python ~/.hermes/scripts/blog_ingest.py
```

## Root Cause Detail

Use the runner-provided profile HOME and canonical `~/wiki`. Do not infer alternate runtime paths.
