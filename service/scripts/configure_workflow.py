"""Configure only the new unpublished prototype workflow, using private secrets."""
import json
from pathlib import Path
from service.config import settings,ROOT
from service.adapters.twin.client import Platform

WORKFLOW='01a19476-5384-704b-9c5e-569fd96f9adf'
VERSION='01a19476-53ae-7412-a2b8-7f33d081b2c0'
PROMPT='63913bd5-fb43-4b97-b83f-1d239fb9e498'
AGENT='923c677d-46a5-4f63-957d-2a31c64806dd'
POST_CLOSE='d3ddc471-8c67-4ecf-bd2d-c5cb3e7a0bd3'
HOST='https://codex-e2e-lab-sg-20261031.fly.dev'
BASE='/versions/'+VERSION
DEFINITIONS=[
 ('verify_carrier','4906cc32-2a91-4749-9303-a794d22a646e','735398d8-6243-480f-907b-7170373c30b2','/carriers/verify',
  [('mc','MC digits stated by the caller.')]),
 ('send_code','a05bbcef-ebdf-477f-9ac0-063dd99a986e','128ce5a8-dace-430b-9435-9af3a49114d3','/otp/send',[]),
 ('verify_code','af17a0af-564e-44da-8136-43fc5696fc94','988796d8-1679-4b2e-8585-47e89f740815','/otp/verify',
  [('code','The six digits the caller actually read. Preserve leading zeros.')]),
 ('find_loads','51153eb0-2461-470e-bb2c-13b119de81c2','ff57cc60-4746-473c-aa23-7089f4df2edd','/loads/search',
  [('equipment','DRY_VAN, REEFER, FLATBED, STEP_DECK or POWER_ONLY.'),('origin_state','Two-letter state, or blank.'),('dest_state','Two-letter state, or blank.')]),
 ('agree_rate','57022450-d36f-4299-9d1e-c1208ace9060','a0d8d721-855c-4cab-957a-d4017d997f74','/negotiate',
  [('load_id','A load from find_loads.'),('rate','Exact whole-number ask, or the current offer on acceptance.')]),
 ('request_booking','b61c7773-017b-4723-bfc0-279bf4c9b5af','ad65981e-a8f5-43ba-b274-fcd4389a4b95','/bookings',[]),
 ('finish_call','59db3288-c43d-4d27-8031-f1048f4ac668','8a3c4072-9543-4a21-bb64-f063f0eca147',None,[])]


def paragraph(text):return [{'type':'paragraph','children':[{'text':text}]}]
def variable(group,name):return '{{$var:'+group+'.'+name+'}}'
def close_url():
    return [{'type':'paragraph','children':[{'text':HOST+'/calls/'},
        {'type':'variable','group_id':'current','variable_id':'run_id','children':[{'text':''}]},{'text':'/close'}]}]


def main():
    values=settings();p=Platform(values)
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
