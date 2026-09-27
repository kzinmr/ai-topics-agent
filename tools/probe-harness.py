#!/usr/bin/env python3
"""Offline startup/protocol probe. Sends no model prompt and no messages."""
import argparse
import os
import tempfile
from pathlib import Path
from ai_topics_agent.adapters import JsonLines,_codex_request

p=argparse.ArgumentParser();p.add_argument('harness',choices=['pi','codex']);args=p.parse_args()
with tempfile.TemporaryDirectory(prefix='wiki-harness-probe-') as temp:
    env=os.environ.copy();env['HOME']=temp;env['HERMES_PROFILE_ROOT']=temp
    env.pop('CODEX_HOME',None);env.pop('PI_CODING_AGENT_DIR',None)
    stream=JsonLines(['codex','app-server'] if args.harness=='codex' else ['pi','--mode','rpc','--no-session'],temp,env,20)
    try:
        if args.harness=='codex':
            result,_=_codex_request(stream,1,'initialize',{'clientInfo':{'name':'ai_topics_probe','version':'0.1.0'}})
            stream.send({'method':'initialized','params':{}})
            print('Codex initialization OK')
        else:
            stream.send({'type':'get_state','id':'probe'})
            while True:
                event=stream.recv()
                if event.get('id')=='probe':
                    if not event.get('success'):raise RuntimeError('pi rejected get_state')
                    print('pi RPC get_state OK');break
    finally:stream.close()
