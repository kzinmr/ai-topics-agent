# HERMES_HOME Symlink Structure (Cron-Mode Pitfall)

## The Symlink Chain

> Historical host repair example retired. Use `ai-topics-agent doctor` and the migration runbook.

Use the runner-provided profile HOME and canonical `~/wiki`. Do not infer alternate runtime paths.

## Debugging Triage Path Issues

When verifying triage JSON exists:

> Historical host repair example retired. Use `ai-topics-agent doctor` and the migration runbook.

## In Python Scripts

For cron-mode scripts written to `/tmp/` and executed via `terminal`:

```python
import os
# CORRECT: use env var
hermes_home = os.environ.get('HERMES_HOME', os.path.expanduser('~/.hermes'))

# ALSO WORKS (but less clear): expanduser resolves through symlink
hermes_home = os.path.expanduser(os.path.expanduser('~/.hermes'))

# Both produce valid paths because the symlink chain is intact
```

The pitfall described in the main skill (`expanduser` resolving to nested path) is **mitigated by the symlink** — the nested path still points to the correct directory. The real risk is if the symlink is broken or removed.
