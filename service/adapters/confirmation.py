"""Conservative booking consent from platform-owned dialogue, never tool arguments."""
import asyncio
import re
from datetime import datetime


def dialogue_turns(messages):
    turns=[]
    for message in messages:
        role=message.get('role');text=message.get('content')
        if role not in ('user','assistant') or not isinstance(text,str) or not text.strip():continue
        if text.startswith('<Thoughts>') or message.get('is_filler'):continue
        if turns and turns[-1]['role']==role:
            turns[-1]['text']+=' '+text
            turns[-1]['id']=message['id']
            turns[-1]['ids'].append(message['id'])
            turns[-1]['interrupted']|=bool(message.get('is_interrupted'))
        else:turns.append({'role':role,'text':text,'id':message['id'],'ids':[message['id']],
                           'interrupted':bool(message.get('is_interrupted'))})
    return turns


def consent_evidence(messages,rate,anchor=None,load_id=None):
    turns=dialogue_turns(messages)
    users=[turn for turn in turns if turn['role']=='user']
    latest=users[-1]['id'] if users else None
    result={'anchor':latest,'approved':False}
    if not anchor or latest==anchor or len(turns)<2:return result
    user,question=turns[-1],turns[-2]
    anchor_positions=[i for i,turn in enumerate(turns) if anchor in turn['ids'] and turn['role']=='user']
    if not anchor_positions or anchor_positions[-1]>=len(turns)-2:return result
    if user['role']!='user' or user['interrupted'] or question['role']!='assistant' or question['interrupted']:return result
    # Do not erase a new amount or question mark and turn it into a bare yes.
    if re.search(r'[0-9$?]',user['text']):return result
    answer=re.sub(r'[.,!]',' ',user['text'].lower())
    answer=' '.join(answer.split())
    positives={'yes','yes please','yes go ahead','yes please go ahead','yes book it',
               'yes please book it','go ahead','go ahead and book it','please book it','book it'}
    if answer not in positives:return result
    amounts='(?:'+re.escape(str(rate))+'|'+re.escape(format(rate,','))+')'
    expected=r'May\s+I\s+book\s+load\s+'+re.escape(load_id or '')+r'\s+at\s+\$'+amounts+r'\s+total\?'
    if load_id and re.fullmatch(expected,question['text'].strip(),re.I):
        result['approved']=True
        result['question_id']=question['id'];result['answer_id']=user['id']
    return result


class NativeConfirmation:
    def __init__(self,platform,workflow_id):self.platform,self.workflow_id=platform,workflow_id

    async def __call__(self,cid,load_id,rate,anchor):
        run=await asyncio.to_thread(self.platform.request,'/runs/'+cid)
        if run.get('workflow_id')!=self.workflow_id:raise ValueError('Unexpected workflow')
        sessions=await asyncio.to_thread(self.platform.request,'/runs/'+cid+'/sessions')
        messages=[]
        for session in sessions.get('data',[]):
            cursor=None;page=1
            for _ in range(20):
                suffix=('?cursor='+cursor) if cursor else ('?page='+str(page))
                path='/sessions/'+session['id']+'/messages'+suffix
                response=await asyncio.to_thread(self.platform.request,path)
                messages.extend(response.get('data',[]))
                cursor=response.get('next_cursor') or (response.get('pagination') or {}).get('next_cursor')
                pagination=response.get('pagination') or {}
                if not cursor and not pagination.get('has_next_page'):break
                page+=1
            else:raise ValueError('Incomplete dialogue')
        def timestamp(message):
            value=message['timestamp']
            try:return float(value)
            except (TypeError,ValueError):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
        messages.sort(key=timestamp)
        return consent_evidence(messages,rate,anchor,load_id)
