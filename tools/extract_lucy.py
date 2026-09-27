#!/usr/bin/env python3
"""One-way, allowlisted extraction of operational source; never reads secrets.

Run against a legacy profile to a NEW output directory, then review changes.
Runtime state and provider configuration are deliberately not imported here.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def normalize(text):
    for old, new in [('/opt/data/home/wiki', '~/wiki'), ('/opt/data/ai-topics/wiki', '~/wiki'),
                     ('/opt/data/wiki', '~/wiki'), ('~/ai-topics/wiki', '~/wiki'),
                     ('/opt/data/ai-topics/scripts', '~/.hermes/scripts'),
                     ('~/ai-topics/scripts', '~/.hermes/scripts'),
                     ('/opt/data/.hermes', '~/.hermes'), ('/opt/data', '~'),
                     ('~/scripts', '~/.hermes/scripts')]:
        text = text.replace(old, new)
    return text


def extract(profile, out):
    repo = profile / 'ai-topics'
    assets = out / 'assets'
    records = []
    def copy(src, dest, prose=False):
        raw = src.read_bytes()
        text = raw.decode('utf-8')
        if prose:
            text = normalize(text)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
        records.append({'source': str(src.relative_to(profile)), 'target': str(dest.relative_to(out)),
                        'sha256': hashlib.sha256(raw).hexdigest()})
    excluded = {'raw_backlog_manual.py', 'discord_slack_relay.py', 'email_watcher.sh', 'sync_cron.sh',
                'wiki-codex-setup.sh', 'wiki-mcp-filesystem.sh', 'wiki-skill-install.sh', 'install_hooks.sh',
                'home_symlink_watchdog.py'}
    for src in sorted((repo/'scripts').iterdir()):
        if src.suffix not in ('.py', '.sh') or src.name in excluded: continue
        live = profile/'.hermes/scripts'/src.name
        chosen = live if live.is_file() else src
        copy(chosen, assets/'scripts'/src.name)
    jobs = json.loads((profile/'.hermes/cron/jobs.json').read_text())['jobs']
    wanted = {s for j in jobs for s in j.get('skills', [])}
    # Include directly referenced companion workflows; avoid copying unrelated personal skills.
    wanted |= {'active-crawl-wiki','wiki-concept-from-research','x-account-enrichment',
               'documentation-page-ingestion','x-article-retrieval','wiki-comparison-page-routing',
               'blogwatcher','wiki-entity-upgrade','grokipedia-enrichment'}
    for name in sorted(wanted):
        candidates = list((repo/'config/hermes/skills').glob('*/'+name+'/SKILL.md'))
        if not candidates: raise ValueError(f'missing skill: {name}')
        base = candidates[0].parent
        for src in sorted(base.rglob('*')):
            if src.is_file() and src.suffix in ('.md','.py','.sh','.json','.yaml','.yml') and '__pycache__' not in src.parts:
                copy(src,assets/'skills'/name/src.relative_to(base),prose=src.suffix=='.md')
    copy(profile/'.hermes/SOUL.md',assets/'SOUL.md',True)
    clean=[]
    chains={'blog-triage':['blog-ingest'],'blog-wiki-ingest':['blog-triage'],
            'newsletter-triage':['newsletter-ingest'],'newsletter-wiki-ingest':['newsletter-triage'],
            'dreaming-group':['dreaming-collect'],'dreaming-wiki-ingest':['dreaming-group']}
    for j in jobs:
        name=re.sub(r'[^a-z0-9]+','-',j['name'].lower()).strip('-')
        prompt=normalize(j.get('prompt',''))
        prompt=re.sub(r'\b\d{16,}\b','${DELIVERY_TARGET}',prompt)
        # Keep machine-readable responses pure. Usage comes from adapter events, never invented token counts.
        prompt=re.sub(r'# TOKEN USAGE TRACKING\nAt the end of your response, print exactly one line:\nCOST_REPORT:[^\n]*\n*','',prompt)
        (assets/'prompts').mkdir(parents=True,exist_ok=True)
        (assets/'prompts'/f'{name}.md').write_text(prompt+'\n')
        clean.append({'name':name,'legacy_name':j['name'],'legacy_id':j['id'],
                      'enabled':j['enabled'],'schedule':j['schedule']['expr'],
                      'script':j.get('script'),'no_agent':j.get('no_agent',False),
                      'skills':j.get('skills',[]),'prompt':f'assets/prompts/{name}.md',
                      'depends_on':chains.get(name,[]),'max_dependency_age_hours':26,
                      'timeout_seconds':3600,'script_timeout_seconds':600,
                      'response_format':'json' if name in ('blog-triage','newsletter-triage','dreaming-group') else 'text',
                      'delivery':'digest' if name=='weekly-ai-digest' else 'hot-posts' if name=='ai-topics-slack-hot-posts' else 'operations',
                      'legacy_max_tokens':j.get('max_tokens')})
    (out/'config').mkdir(parents=True,exist_ok=True)
    (out/'config/jobs.json').write_text(json.dumps({'version':1,'timezone':'UTC','jobs':clean},ensure_ascii=False,indent=2)+'\n')
    (out/'docs').mkdir(parents=True,exist_ok=True)
    (out/'docs/source-inventory.json').write_text(json.dumps({'source_repository':'https://github.com/kzinmr/ai-topics',
        'source_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
        'source_is_live_worktree':True,'files':records,'excluded_scripts':sorted(excluded)},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('profile',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();extract(a.profile,a.output)
