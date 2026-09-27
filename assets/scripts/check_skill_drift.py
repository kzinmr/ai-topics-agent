#!/usr/bin/env python3
"""Compare installed portable skill assets with their deployment manifest."""
import hashlib
import json
import os
from pathlib import Path
from portable_paths import profile_root


def main():
    root=profile_root();manifest=root/'.ai-topics-agent/assets.json'
    if not manifest.exists():raise SystemExit('asset manifest missing: run ai-topics-agent init')
    drifted=[];checked=0
    for name,digest in json.loads(manifest.read_text()).items():
        if not name.startswith('.hermes/skills-portable/'):continue
        checked+=1;path=root/name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:drifted.append(name)
    print(json.dumps({'checked':checked,'drifted':drifted,'status':'drift' if drifted else 'in_sync'},indent=2))

if __name__=='__main__':main()
