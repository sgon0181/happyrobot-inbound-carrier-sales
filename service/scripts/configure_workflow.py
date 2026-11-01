"""Configure only the new unpublished prototype workflow, using private secrets."""
import json
from pathlib import Path
from service.config import settings,ROOT
from service.scripts.cli_platform import CliPlatform as Platform

WORKFLOW='01a19476-5384-704b-9c5e-569fd96f9adf'
VERSION='01a194ae-0d43-7970-84c7-69c591936a37'
PROMPT='01a194ae-0d59-7710-a523-a6d129e5cae6'
AGENT='01a194ae-0d54-7b1a-9a1d-70c79853b4f6'
POST_CLOSE='01a194ae-0d58-78c8-ac64-178ce8a0f36e'
HOST='https://codex-e2e-lab-sg-20261031.fly.dev'
BASE='/versions/'+VERSION
DEFINITIONS=[
 ('verify_carrier','01a194ae-0d5a-71e2-9cad-512d0e77432c','01a194ae-0d4f-7ee9-8a97-5047290f1877','/carriers/verify',
  [('mc','MC digits stated by the caller.')]),
 ('send_code','01a194ae-0d5b-7405-b94f-da48fa187079','01a194ae-0d50-79d7-927e-1c0107abcbbe','/otp/send',[]),
 ('verify_code','01a194ae-0d5c-7f6c-8f30-075b184b212b','01a194ae-0d52-7e57-b8f8-830a993aaaed','/otp/verify',
  [('code','The six digits the caller actually read. Preserve leading zeros.')]),
 ('find_loads','01a194ae-0d5d-74a9-bbda-fe71d41e65ca','01a194ae-0d4e-701a-98ae-2330360b6027','/loads/search',
  [('equipment','DRY_VAN, REEFER, FLATBED, STEP_DECK or POWER_ONLY.'),('origin_state','Two-letter state, or blank.'),('dest_state','Two-letter state, or blank.')]),
 ('agree_rate','01a194ae-0d5e-7640-a695-8a16d346fba6','01a194ae-0d53-70ae-b56c-ad794c5c96fc','/negotiate',
  [('load_id','A load from find_loads.'),('rate','Exact whole-number ask, or the current offer on acceptance.')]),
 ('request_booking','01a194ae-0d5f-7f4c-b723-4e9f6a527a8d','01a194ae-0d55-776c-9dbd-1ced052edc9f','/bookings',[]),
 ('finish_call','01a194ae-0d60-74b5-bee4-01c632e9cc67','01a194ae-0d55-7de2-b5c3-c93e91d12dd6',None,[])]


def paragraph(text):return [{'type':'paragraph','children':[{'text':text}]}]
def variable(group,name):return '{{$var:'+group+'.'+name+'}}'
def close_url():
    return [{'type':'paragraph','children':[{'text':HOST+'/calls/'},
        {'type':'variable','group_id':'current','variable_id':'run_id','children':[{'text':''}]},{'text':'/close'}]}]


def main():
    values=settings();p=Platform(values)
    response=p.request('/versions/'+VERSION);version=response.get('data',response)
    if version.get('is_live') or version.get('is_published'):
        raise RuntimeError('Fork the prototype to a writable version and refresh its node IDs before configuring')
    path='/workflows/'+WORKFLOW+'/variables'
    existing=p.request(path)['data']
    key='PROTOTYPE_AGENT_KEY'
    if not any(v['key']==key for v in existing):
        result=p.request(path,{'key':key,'value_development':values['AGENT_API_KEY'],
            'value_staging':values['AGENT_API_KEY'],'value_production':values['AGENT_API_KEY'],'is_hidden_in_ui':True})
        print('Private prototype workflow key configured')
    token=[{'type':'paragraph','children':[{'type':'variable','children':[{'text':''}],
               'group_id':'use_case_variables','variable_id':key}]}]
    schema={'status':'SCHEMA_EXAMPLE','carrier_name':'SCHEMA_EXAMPLE','code_passed':False,
        'channel':'email','destination':'configured demo inbox','offer':1000,'round':1,'final':False,
        'rate':1000,'agreed_rate':1000,'load_id':'SCHEMA_EXAMPLE','handoff_allowed':False,'outcome':'SCHEMA_EXAMPLE',
        'confirmation_prompt':'May I book load SCHEMA_EXAMPLE at $1000 total?',
        'loads':[{'load_id':'SCHEMA_EXAMPLE','origin_city':'SCHEMA_EXAMPLE','origin_state':'TX',
                  'destination_city':'SCHEMA_EXAMPLE','destination_state':'GA','pickup_datetime':'2099-01-01T00:00:00Z',
                  'delivery_datetime':'2099-01-02T00:00:00Z','equipment_type':'DRY_VAN','offer':1000,
                  'weight':42000,'commodity_type':'Freight','num_of_pieces':20,'miles':800,
                  'dimensions':'636 x 96 x 108 in','notes':'SCHEMA_EXAMPLE'}]}
    for name,tool,action,route,parameters in DEFINITIONS:
        function={'description':paragraph('Call '+name+' in the required verification, matching, negotiation and handoff order. Only the backend decides.'),
            'parameters':[{'name':k,'description':paragraph(d),'required':k not in ('origin_state','dest_state'),
                           'binding':{'mode':'agent'}} for k,d in parameters],'message':{'type':'none'}}
        p.request(BASE+'/nodes/'+tool,{'type':'tool','name':name,'function':function},'PUT')
        body={'run_id':variable('current','run_id')}
        for field,_ in parameters:body[field]=variable(tool,field)
        raw='{'+','.join(json.dumps(k)+':'+v for k,v in body.items())+'}'
        config={'url':paragraph(HOST+route) if route else close_url(),
            'body':{'raw':raw,'contentType':'application/json','schemaVersion':2},
            'token':token,'authType':'bearer','ignore5XX':False,'ignoreTimeouts':False,'webhookSchemaVersion':2}
        p.request(BASE+'/nodes/'+action,{'type':'action','event_id':'01926f2b-2973-7ebf-ada1-e984251e27ec',
                                       'name':'Prototype '+name,'configuration':config},'PUT')
        p.request(BASE+'/nodes/'+action+'/custom-output',{'data':schema},'PUT')
        inspect=p.request(BASE+'/tools/'+tool+'/tool-call-result/inspect',{})
        nodes=inspect.get('nodes',inspect.get('data',{}).get('nodes',[]) if isinstance(inspect.get('data'),dict) else [])
        exposed=[]
        for node in nodes:
            if node.get('node_id',node.get('id'))==action:exposed=[f['path'] for f in node.get('fields',[])]
        if not exposed:raise RuntimeError('Tool result schema was not available')
        p.request(BASE+'/tools/'+tool+'/tool-call-result/visibility',{'node_id':action,'exposed_fields':exposed},'PUT')
        print(name,'configured;',len(exposed),'safe fields')
    p.request(BASE+'/nodes/'+POST_CLOSE,{'type':'action','event_id':'01926f2b-2973-7ebf-ada1-e984251e27ec',
        'name':'Prototype post-call close','configuration':{'url':close_url(),
        'body':{'raw':'{"run_id":'+variable('current','run_id')+'}','contentType':'application/json','schemaVersion':2},
        'token':token,'authType':'bearer','ignore5XX':False,'ignoreTimeouts':False,'webhookSchemaVersion':2}},'PUT')
    text=(ROOT/'happyrobot/prototype-prompt.txt').read_text()
    p.request(BASE+'/nodes/'+PROMPT,{'type':'prompt','prompt_md':text,
        'initial_message':paragraph('Hi, this is the carrier sales prototype. What is your MC number?')},'PUT')
    agent=p.request(BASE+'/nodes/'+AGENT)['data'];config=agent['configuration']
    config.update(disable_hangup=False,max_call_duration=540,max_silence_hold_duration=60)
    p.request(BASE+'/nodes/'+AGENT,{'type':'agent','event_id':agent['event_id'],'configuration':config},'PUT')
    print('Prototype workflow configured, still unpublished')


if __name__=='__main__':main()
