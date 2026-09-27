"""Shared path contract; .hermes paths are a disk compatibility ABI only."""
import os
from pathlib import Path

def profile_root():
    return Path(os.environ.get('HERMES_PROFILE_ROOT') or os.environ.get('HERMES_SUBPROCESS_HOME') or Path.home()).expanduser()

def wiki_root():
    return Path(os.environ.get('WIKI_ROOT') or profile_root()/'wiki').expanduser()

def repo_root():
    return Path(os.environ.get('AI_TOPICS_REPO') or profile_root()/'ai-topics').expanduser()
