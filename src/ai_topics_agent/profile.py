"""Materialize code, never silently overwrite live configuration or content."""
import hashlib
import json
import os
import shutil
import subprocess
from .config import atomic_write,json_write


def initialize(cfg,content_source=None,clone=False):
    marker=cfg.state/'profile.json'
    if marker.exists():raise ValueError('profile already initialized; use sync-assets')
    if (cfg.hermes/'config.yaml').exists() or (cfg.hermes/'cron/jobs.json').exists():
        raise ValueError('refuse to initialize a live Hermes profile; use a new destination')
    if cfg.repo.exists():raise ValueError('destination content repository already exists')
    cfg.profile.mkdir(parents=True,exist_ok=True)
    cfg.state.mkdir(mode=0o700,exist_ok=True)
    if content_source:
        subprocess.run(['git','clone','--no-hardlinks',str(content_source),str(cfg.repo)],check=True)
        subprocess.run(['git','-C',str(cfg.repo),'remote','set-url','origin','https://github.com/kzinmr/ai-topics.git'],check=True)
    elif clone:
        subprocess.run(['git','clone','https://github.com/kzinmr/ai-topics.git',str(cfg.repo)],check=True)
    else:
        (cfg.repo/'wiki').mkdir(parents=True)
    if cfg.wiki.exists() or cfg.wiki.is_symlink():raise ValueError('wiki path already exists')
    cfg.wiki.symlink_to('ai-topics/wiki',target_is_directory=True)
    for name in ['cron/data','cron/output','scripts','bin']:(cfg.hermes/name).mkdir(parents=True,exist_ok=True)
    json_write(cfg.hermes/'cron/jobs.json',{'jobs':[]})
    # Provider and auth setup remain explicit and private, not copied from the original host.
    atomic_write(cfg.hermes/'config.yaml',json.dumps({'terminal':{'backend':'local','cwd':str(cfg.repo)},
        'skills':{'external_dirs':['~/.hermes/skills-portable']},'timezone':'UTC'},indent=2)+'\n')
    json_write(marker,{'version':1,'profile':'lucy','scheduler':'ai-topics-agent'})
    original=cfg.repo/'AGENTS.md'
    if original.exists():
        atomic_write(cfg.state/'legacy-content-AGENTS.md',original.read_text())
        original.unlink()
    sync_assets(cfg)
    if not cfg.local_path.exists():
        json_write(cfg.local_path,json.loads((cfg.source/'config/local.example.json').read_text()))
    if (cfg.repo/'.git').exists():
        subprocess.run(['git','-C',str(cfg.repo),'config','core.hooksPath','.githooks'],check=True)
    return {'profile':str(cfg.profile),'content':str(cfg.repo),'initialized':True}


def sync_assets(cfg):
    if not (cfg.state/'profile.json').exists():raise ValueError('profile must be initialized first')
    manifest_path=cfg.state/'assets.json'
    previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    planned={'ai-topics/AGENTS.md':(cfg.source/'assets/AGENTS.md').read_bytes()}
    for source in (cfg.source/'assets/scripts').iterdir():
        if source.is_file():planned['.hermes/scripts/'+source.name]=source.read_bytes()
    planned['.hermes/SOUL.md']=(cfg.source/'assets/SOUL.md').read_bytes()
    for source in (cfg.source/'assets/skills').rglob('*'):
        if source.is_file() and '__pycache__' not in source.parts:
            planned['.hermes/skills-portable/'+str(source.relative_to(cfg.source/'assets/skills'))]=source.read_bytes()
    # Validate every destination before the first write.
    for relative in planned:
        dest=cfg.profile/relative
        if dest.is_symlink():raise ValueError(f'refuse symlink asset: {relative}')
        if dest.exists():
            digest=hashlib.sha256(dest.read_bytes()).hexdigest()
            if digest != previous.get(relative) and dest.read_bytes()!=planned[relative]:
                raise ValueError(f'local asset changed; reconcile before sync: {relative}')
    hashes={}
    for relative,data in planned.items():
        dest=cfg.profile/relative
        atomic_write(dest,data.decode(),0o755 if relative.endswith('.sh') else 0o644)
        hashes[relative]=hashlib.sha256(data).hexdigest()
    # Retire only unchanged files previously managed by this installer.
    for relative,digest in previous.items():
        if relative in planned:continue
        dest=cfg.profile/relative
        if dest.is_file() and not dest.is_symlink() and hashlib.sha256(dest.read_bytes()).hexdigest()==digest:dest.unlink()
    json_write(manifest_path,hashes)
    return {'assets':len(hashes)}
