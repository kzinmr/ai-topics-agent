"""Minimal protocol peer, deliberately independent of adapter implementation."""
import json
import os
import sys
import time

def send(value):print(json.dumps(value),flush=True)
mode=sys.argv[1];scenario=sys.argv[2] if len(sys.argv)>2 else 'ok'
if scenario=='timeout':time.sleep(20);raise SystemExit()
for line in sys.stdin:
    data=json.loads(line)
    if mode=='codex':
        method=data.get('method')
        if method=='initialize':send({'id':data['id'],'result':{'userAgent':'fixture'}})
        elif method=='thread/start':send({'id':data['id'],'result':{'thread':{'id':'thread-fixture'}}})
        elif method=='turn/start':
            assert data['params']['sandboxPolicy']['type']=='workspaceWrite'
            assert data['params']['approvalPolicy']=='never'
            if scenario=='reject':send({'id':data['id'],'error':{'code':-1,'message':'invalid model'}});continue
            send({'id':data['id'],'result':{'turn':{'id':'turn-fixture'}}})
            if scenario=='approval':
                send({'id':99,'method':'item/commandExecution/requestApproval','params':{}});continue
            if scenario=='eof':raise SystemExit()
            send({'method':'item/completed','params':{'threadId':'thread-fixture','item':{'id':'commentary','type':'agentMessage','text':'working'}}})
            send({'method':'item/agentMessage/delta','params':{'delta':'not authoritative'}})
            send({'method':'item/completed','params':{'threadId':'thread-fixture','item':{'id':'answer','type':'agentMessage','text':'{"decisions": [], "ok": true}'}}})
            send({'method':'turn/completed','params':{'threadId':'thread-fixture','turn':{'id':'turn-fixture','status':'failed' if scenario=='failure' else 'completed','error':None}}})
    else:
        assert data['type']=='prompt'
        send({'type':'response','id':'run','command':'prompt','success':scenario!='reject','error':'rejected' if scenario=='reject' else None})
        if scenario=='eof':raise SystemExit()
        if scenario=='approval':send({'type':'extension_ui_request','id':'question'});continue
        msg={'role':'assistant','content':[{'type':'text','text':'{"decisions": [], "ok": true}'}],'stopReason':'error' if scenario=='failure' else 'stop','usage':{'input':12,'output':8}}
        send({'type':'message_end','message':msg});send({'type':'agent_end','messages':[msg]});send({'type':'agent_settled'})
