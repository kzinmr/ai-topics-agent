import hashlib
import importlib.util
import json
import os
import shutil
from .config import inside


def doctor(cfg,job=None):
    checks=[]
    def check(name,ok,detail=''):checks.append({'name':name,'ok':bool(ok),'detail':detail})
    check('initialized',(cfg.state/'profile.json').is_file())
    check('canonical-wiki',cfg.wiki.is_dir() and cfg.wiki.resolve()==(cfg.repo/'wiki').resolve())
    for name in ('SCHEMA.md','index.md','log.md'):check('wiki/'+name,(cfg.wiki/name).is_file())
    native=cfg.hermes/'cron/jobs.json'
    check('single-scheduler',not native.exists() or not any(j.get('enabled',True) for j in json.loads(native.read_text()).get('jobs',[])))
    selected=[cfg.job(job)] if job else [j for j in cfg.jobs if j['enabled']]
    env=cfg.env()
    for mod in ('bs4','httpx','readability','yaml','requests'):
        check('python:'+mod,importlib.util.find_spec(mod) is not None,'Install .[collectors] in the runner Python environment')
    names={j['name'] for j in selected}
    for binary,needed in [('git',True),('bash',True),('blogwatcher-cli','blog-ingest' in names),('xurl',bool(names & {'x-bookmarks-ingest','x-accounts-scan','trending-topics'}))]:
        if needed:check('binary:'+binary,shutil.which(binary,path=env['PATH']) is not None)
    if 'newsletter-ingest' in names:
        for name in ('EMAIL_IMAP_HOST','EMAIL_ADDRESS','EMAIL_PASSWORD'):check('secret:'+name,bool(env.get(name)))
    if 'ai-topics-slack-hot-posts' in names:
        for name in ('SLACK_BOT_TOKEN','AI_TOPICS_SLACK_CHANNEL_ID'):check('secret:'+name,bool(env.get(name)))
    name=cfg.local.get('harness','hermes')
    if name=='pi' and any(not j['no_agent'] for j in selected):
        check('web-search',bool(env.get('BRAVE_API_KEY') or env.get('WIKI_SEARCH_COMMAND')),'Set BRAVE_API_KEY or WIKI_SEARCH_COMMAND for research jobs')
    options=cfg.local.get('adapters',{}).get(name,{})
    executable=options.get('executable','hermes') if name=='hermes' else options.get('command',[name])[0]
    if any(not j['no_agent'] for j in selected):check('harness:'+name,shutil.which(executable,path=env['PATH']) is not None)
    manifest=cfg.state/'assets.json'
    if manifest.exists():
        changed=[]
        for relative,digest in json.loads(manifest.read_text()).items():
            path=inside(cfg.profile,relative)
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:changed.append(relative)
        check('managed-assets',not changed,','.join(changed[:20]))
    else:check('managed-assets',False,'run init')
    secrets=cfg.state/'secrets.json'
    if secrets.exists():check('secret-file-permissions',secrets.stat().st_mode & 0o077==0,'chmod 600 secrets.json')
    return {'ok':all(c['ok'] for c in checks),'checks':checks,
            'notes':['Credentials are checked for presence, not network authentication. Delivery defaults to a local outbox.']}
