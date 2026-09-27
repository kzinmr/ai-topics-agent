"""Allowlisted state bundles with SQLite online backup and verified, bounded restore.

Secrets and harness sessions are excluded. A consistent cutover requires source
writers to be stopped; rehearsal snapshots explicitly record weaker consistency.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from pathlib import Path,PurePosixPath
from .config import json_write,atomic_write,inside
from .state import profile_lock


def selected(profile,content=False):
    files=[]
    for base in ('.hermes/cron/data','.hermes/cron/output','.hermes/scripts/cache','.ai-topics-agent/runs','.ai-topics-agent/outbox'):
        root=profile/base
        if root.exists():files += [p for p in root.rglob('*') if p.is_file() and not p.is_symlink()]
    files += [p for p in (profile/'.hermes').glob('processed_*.json') if p.is_file() and not p.is_symlink()]
    for name in ('.blogwatcher/blogwatcher.db','.ai-topics-agent/runs.db'):
        p=profile/name
        if p.is_file() and not p.is_symlink():files.append(p)
    if content:
        files += [p for p in (profile/'ai-topics').rglob('*') if p.is_file() and not p.is_symlink()
                  and '.git' not in p.relative_to(profile/'ai-topics').parts
                  and not any(x in p.parts for x in ('__pycache__','.venv','node_modules'))
                  and not p.name.startswith('.env') and p.name not in ('.git-credentials','.netrc','AGENTS.md')]
    return sorted(set(files))


def snapshot(profile,destination,*,quiesced=False,include_content=False):
    profile=profile.resolve();destination=destination.resolve()
    if destination.exists():raise ValueError('snapshot destination already exists')
    if destination.is_relative_to(profile):raise ValueError('snapshot must be outside the profile')
    destination.parent.mkdir(parents=True,exist_ok=True)
    manifest={'version':1,'profile_root':str(profile),'legacy_roots':['/opt/data'],
              'consistency':'quiesced' if quiesced else 'rehearsal', 'includes_content':include_content,'files':{}}
    if include_content and (profile/'ai-topics/.git').exists():
        tracked=subprocess.check_output(['git','-C',str(profile/'ai-topics'),'ls-files','-z']).decode().split('\0')
        manifest['deleted_content']=['ai-topics/'+name for name in tracked if name and not (profile/'ai-topics'/name).exists()
                                     and allowed('ai-topics/'+name,True)]
    with tempfile.TemporaryDirectory(prefix='wiki-snapshot-') as temp:
        stage=Path(temp)
        for source in selected(profile,include_content):
            if not source.resolve().is_relative_to(profile):raise ValueError('source symlink escape')
            rel=source.relative_to(profile);target=stage/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if source.suffix=='.db':
                # URI quoting handles spaces, # and ? in profile locations.
                src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
                dst=sqlite3.connect(target)
                try:src.backup(dst)
                finally:src.close();dst.close()
            else:shutil.copy2(source,target)
            os.chmod(target,0o600)
            manifest['files'][str(rel)]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':target.stat().st_size}
        # Schedule definitions stay in Git. Only allowlisted status fields travel.
        jobs=profile/'.hermes/cron/jobs.json'
        if jobs.exists():
            data=json.loads(jobs.read_text())
            manifest['legacy_status']=[{k:j.get(k) for k in ('id','name','last_run_at','last_status')} for j in data.get('jobs',[])]
        json_write(stage/'manifest.json',manifest)
        fd,tmp=tempfile.mkstemp(prefix='.snapshot-',dir=destination.parent);os.close(fd)
        try:
            os.chmod(tmp,0o600)
            with tarfile.open(tmp,'w:gz') as tar:
                tar.add(stage/'manifest.json',arcname='manifest.json')
                for name in manifest['files']:tar.add(stage/name,arcname=name,recursive=False)
            os.replace(tmp,destination)
        finally:Path(tmp).unlink(missing_ok=True)
    return {'path':str(destination),'files':len(manifest['files']),'consistency':manifest['consistency']}


def relocate(value,roots,dest):
    if isinstance(value,str):
        # Rewrite path fields only. Do not rewrite URLs or arbitrary embedded article text.
        for root in sorted(roots,key=len,reverse=True):
            if value==root or value.startswith(root+'/'):return str(dest)+value[len(root):]
        return value
    if isinstance(value,list):return [relocate(v,roots,dest) for v in value]
    if isinstance(value,dict):return {k:relocate(v,roots,dest) for k,v in value.items()}
    return value


def allowed(name,content):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:return False
    prefixes=('.hermes/cron/data/','.hermes/cron/output/','.hermes/scripts/cache/',
              '.ai-topics-agent/runs/','.ai-topics-agent/outbox/')
    return (name.startswith(prefixes) or (name.startswith('.hermes/processed_') and len(p.parts)==2 and name.endswith('.json'))
            or name in ('.blogwatcher/blogwatcher.db','.ai-topics-agent/runs.db')
            or (content and name.startswith('ai-topics/') and '.git' not in p.parts
                and not p.name.startswith('.env') and p.name not in ('.git-credentials','.netrc','AGENTS.md')))


def restore(cfg,bundle,*,rehearsal=False,max_bytes=2*1024**3):
    if not (cfg.state/'profile.json').exists():raise ValueError('initialize a fresh destination before restore')
    with profile_lock(cfg.state),tempfile.TemporaryDirectory(prefix='wiki-restore-') as temp:
        if (cfg.state/'restored.json').exists() or (cfg.state/'runs.db').exists():
            raise ValueError('refuse restore over existing runtime state')
        stage=Path(temp)
        with tarfile.open(bundle,'r:gz') as tar:
            members=tar.getmembers()
            if len({m.name for m in members})!=len(members):raise ValueError('duplicate archive entries')
            if any(not m.isfile() for m in members):raise ValueError('archive contains links or special files')
            if sum(m.size for m in members)>max_bytes:raise ValueError('archive exceeds restore size limit')
            manifest=json.load(tar.extractfile('manifest.json'))
            if manifest.get('version')!=1:raise ValueError('unsupported snapshot version')
            if manifest.get('consistency')!='quiesced' and not rehearsal:raise ValueError('rehearsal snapshot requires --rehearsal; do not use for cutover')
            expected=set(manifest['files'])|{'manifest.json'}
            if {m.name for m in members}!=expected:raise ValueError('archive/manifest mismatch')
            for name,meta in manifest['files'].items():
                if not allowed(name,manifest.get('includes_content')):raise ValueError(f'forbidden archive path: {name}')
                data=tar.extractfile(name).read()
                if len(data)!=meta['size'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:raise ValueError(f'checksum mismatch: {name}')
                path=inside(stage,name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            roots=[manifest['profile_root']]+manifest.get('legacy_roots',[])
            # Relocate checkpoints and structured output, not immutable raw source files.
            for name in manifest['files']:
                path=stage/name
                if name.startswith('ai-topics/'):continue
                if path.suffix=='.json':
                    try:data=json.loads(path.read_text())
                    except (UnicodeDecodeError,ValueError):continue
                    json_write(path,relocate(data,roots,cfg.profile))
                elif name.startswith('.hermes/cron/output/') and path.suffix=='.md':
                    text=path.read_text();head,sep,body=text.partition('## Response')
                    if sep:
                        from .runner import parse_json_response
                        try:obj=parse_json_response(body)
                        except ValueError:continue
                        atomic_write(path,head+sep+'\n\n'+json.dumps(relocate(obj,roots,cfg.profile),ensure_ascii=False,indent=2)+'\n')
        deleted=manifest.get('deleted_content',[])
        for name in deleted:
            if not name.startswith('ai-topics/') or not allowed(name,True):raise ValueError('forbidden content deletion')
            target=inside(cfg.profile,name)
            if target.exists() and not target.is_file():raise ValueError('content deletion is not a file')
        # All archive members validated before any destination writes.
        for name in manifest['files']:
            target=inside(cfg.profile,name)
            if target.exists() and not name.startswith('ai-topics/'):
                raise ValueError(f'refuse overwrite of existing state: {name}')
        for name in manifest['files']:
            target=inside(cfg.profile,name);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(stage/name,target);os.chmod(target,0o600)
        for name in deleted:inside(cfg.profile,name).unlink(missing_ok=True)
        from .state import Store
        store=Store(cfg.state)
        try:
            if not (stage/'.ai-topics-agent/runs.db').exists():
                for row in manifest.get('legacy_status',[]):
                    job=next((j for j in cfg.jobs if j['legacy_id']==row.get('id')),None)
                    if job and row.get('last_run_at'):
                        run='import-'+row['id'];store.start(run,job['name'],row['last_run_at'])
                        store.finish(run,row['last_run_at'],'ok' if row['last_status']=='ok' else 'error',{'imported':True})
            # A migrated scheduler starts now; historical slots are not replayed.
            from datetime import datetime,timezone
            store.set_meta('cursor',datetime.now(timezone.utc).replace(second=0,microsecond=0).isoformat())
            store.view(cfg)
        finally:store.close()
        json_write(cfg.state/'restored.json',{'bundle_sha256':hashlib.sha256(Path(bundle).read_bytes()).hexdigest(),
                   'files':len(manifest['files']),'consistency':manifest['consistency']})
    return {'restored':len(manifest['files']),'profile':str(cfg.profile)}
