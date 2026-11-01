"""Read-only sanitized snapshot of the isolated prototype workflow."""
import json
from service.config import settings,ROOT
from service.scripts.cli_platform import CliPlatform as Platform
from service.scripts.configure_workflow import WORKFLOW,VERSION,PROMPT,AGENT,POST_CLOSE,DEFINITIONS


def main():
    values=settings();p=Platform(values)
    response=p.request('/versions/'+VERSION);version=response.get('data',response)
    ids=['01a194ae-0d4c-75f7-beb4-cd07c1bb9dd8',PROMPT,AGENT,POST_CLOSE]
    for _,tool,action,_,_ in DEFINITIONS:ids.extend([tool,action])
    nodes=[]
    for identity in ids:
        node=p.request('/versions/'+VERSION+'/nodes/'+identity)['data']
        node.pop('node_output',None)
        nodes.append(node)
    result={'workflow_id':WORKFLOW,'version_id':VERSION,'version_slug':version.get('slug'),
            'workflow_slug':'yhcdrf4kne4j','web_call_url':'https://platform.happyrobot.ai/deployments/yhcdrf4kne4j',
            'source':'Read-only platform snapshot','version':version,'nodes':nodes}
    text=json.dumps(result,indent=2)
    for key,value in values.items():
        if any(k in key for k in ('KEY','SECRET','TOKEN','PASSWORD')) and isinstance(value,str) and len(value)>10:
            text=text.replace(value,'[REDACTED]')
    (ROOT/'happyrobot/prototype-workflow.json').write_text(text+'\n')
    print('Sanitized workflow snapshot saved:',len(nodes),'nodes')


if __name__=='__main__':main()
