"""Harness transports. The scheduler, scripts, persistence and delivery live elsewhere.

Protocol references and tested versions: docs/harnesses.md.
"""
from __future__ import annotations
import json
import queue
import subprocess
import threading
import time
from .process import execute, stop


class JsonLines:
    def __init__(self,argv,cwd,env,timeout):
        self.deadline=time.monotonic()+timeout
        self.proc=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,text=True,bufsize=1,start_new_session=True)
        self.messages=queue.Queue();self.stderr=[]
        def read():
            try:
                for line in self.proc.stdout:
                    try:self.messages.put(json.loads(line))
                    except ValueError:self.messages.put(RuntimeError('non-JSON harness output'))
            finally:self.messages.put(EOFError('harness closed before completion'))
        def errors():
            for line in self.proc.stderr:
                self.stderr.append(line)
                if len(self.stderr)>100:self.stderr.pop(0)
        self.read_thread=threading.Thread(target=read,daemon=True)
        self.err_thread=threading.Thread(target=errors,daemon=True)
        self.read_thread.start();self.err_thread.start()
    def send(self,message):
        self.proc.stdin.write(json.dumps(message,ensure_ascii=False)+'\n');self.proc.stdin.flush()
    def recv(self):
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('harness deadline exceeded')
        try:message=self.messages.get(timeout=remaining)
        except queue.Empty:raise TimeoutError('harness deadline exceeded') from None
        if isinstance(message,Exception):raise message
        return message
    def close(self):
        stop(self.proc)
        self.read_thread.join(timeout=2);self.err_thread.join(timeout=2)
        for pipe in (self.proc.stdin,self.proc.stdout,self.proc.stderr):pipe.close()


def _codex_request(stream,id,method,params):
    stream.send({'id':id,'method':method,'params':params})
    pending=[]
    while True:
        event=stream.recv()
        if event.get('id')==id and 'method' not in event:
            if 'error' in event:raise RuntimeError(f'Codex {method}: {event["error"]}')
            return event.get('result',{}),pending
        reject_server_request(stream,event)
        pending.append(event)


def reject_server_request(stream,event):
    if 'id' in event and 'method' in event:
        method=event['method']
        if method in ('item/commandExecution/requestApproval','item/fileChange/requestApproval'):
            stream.send({'id':event['id'],'result':{'decision':'decline'}})
        else:
            stream.send({'id':event['id'],'error':{'code':-32601,'message':'Unattended runner does not support interactive requests'}})
        raise RuntimeError(f'harness requires operator interaction: {method}')


def codex(argv,prompt,cwd,env,timeout,options):
    stream=JsonLines(argv,cwd,env,timeout)
    try:
        _codex_request(stream,1,'initialize',{'clientInfo':{'name':'ai_topics_agent','version':'0.1.0'}})
        stream.send({'method':'initialized','params':{}})
        params={'cwd':str(cwd),'approvalPolicy':'never','sandbox':'workspace-write'}
        if options.get('model'):params['model']=options['model']
        result,_=_codex_request(stream,2,'thread/start',params)
        thread=result['thread']['id']
        policy={'type':'workspaceWrite','writableRoots':[env['HERMES_PROFILE_ROOT']],
                'networkAccess':options.get('network_access',True)}
        turn,early=_codex_request(stream,3,'turn/start',{'threadId':thread,
            'input':[{'type':'text','text':prompt}], 'cwd':str(cwd),'approvalPolicy':'never','sandboxPolicy':policy})
        turn_id=turn['turn']['id']; messages={};usage={}
        while True:
            event=early.pop(0) if early else stream.recv()
            reject_server_request(stream,event)
            p=event.get('params',{}); method=event.get('method')
            if p.get('threadId',thread)!=thread:continue
            if method=='item/completed' and p.get('item',{}).get('type')=='agentMessage':
                item=p['item'];messages[item['id']]=item.get('text','')
            if method=='thread/tokenUsage/updated':usage=p.get('tokenUsage',{})
            if method=='turn/completed' and p.get('turn',{}).get('id')==turn_id:
                if p['turn'].get('status')!='completed':raise RuntimeError(f'Codex turn failed: {p["turn"].get("error")}')
                return {'text':list(messages.values())[-1] if messages else '', 'thread_id':thread,'usage':usage}
    finally:stream.close()


def pi(argv,prompt,cwd,env,timeout,options):
    stream=JsonLines(argv,cwd,env,timeout)
    try:
        stream.send({'id':'run','type':'prompt','message':prompt})
        text='';usage={};accepted=False;failure=None
        while True:
            event=stream.recv();kind=event.get('type')
            if kind=='response' and event.get('id')=='run':
                if not event.get('success'):raise RuntimeError(f'pi prompt rejected: {event.get("error")}')
                accepted=True
                if event.get('data',{}).get('disposition')=='handled':
                    raise RuntimeError('pi extension handled the prompt without an agent run')
            if kind=='extension_ui_request':raise RuntimeError('pi extension requested interactive input')
            if kind=='message_end':
                msg=event.get('message',{})
                if msg.get('role')=='assistant':
                    failure=msg.get('errorMessage',msg.get('stopReason')) if msg.get('stopReason') in ('error','aborted') else None
                    text=''.join(c.get('text','') for c in msg.get('content',[]) if c.get('type')=='text')
                    usage=msg.get('usage',{})
            if kind=='agent_end':
                if not accepted:raise RuntimeError('pi ended before accepting prompt')
                # agent_end may carry the authoritative messages (older releases).
                for msg in event.get('messages',[]):
                    if msg.get('role')=='assistant':
                        failure=msg.get('errorMessage',msg.get('stopReason')) if msg.get('stopReason') in ('error','aborted') else None
                        text=''.join(c.get('text','') for c in msg.get('content',[]) if c.get('type')=='text')
                        usage=msg.get('usage',usage)
            if kind=='agent_settled':
                if failure:raise RuntimeError(f'pi assistant failed: {failure}')
                if not accepted:raise RuntimeError('pi settled before accepting prompt')
                return {'text':text,'usage':usage}
    finally:stream.close()


def run_agent(cfg,prompt,timeout):
    name=cfg.local.get('harness','hermes');options=cfg.local.get('adapters',{}).get(name,{})
    env=cfg.env()
    if name=='hermes':
        # Every external Hermes invocation goes through the repository wrapper.
        argv=[str(cfg.source/'bin/hermes-lucy'),'--oneshot',prompt]
        if options.get('model'):argv+=['--model',options['model']]
        if options.get('provider'):argv+=['--provider',options['provider']]
        env['HERMES_RUNTIME']='host'
        env['HERMES_HOST_BIN']=options.get('executable','hermes')
        text=execute(argv,cwd=cfg.repo,env=env,timeout=timeout)
        return {'text':text,'usage':None}
    argv=options.get('command', ['pi','--mode','rpc','--no-session'] if name=='pi' else ['codex','app-server'])
    if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv):
        raise ValueError('adapter command must be a nonempty argv array')
    return (pi if name=='pi' else codex)(argv,prompt,cfg.repo,env,timeout,options)
