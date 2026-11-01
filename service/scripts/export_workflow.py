"""Read-only sanitized snapshot of the isolated prototype workflow."""
import json
from service.config import settings,ROOT
from service.scripts.cli_platform import CliPlatform as Platform
from service.scripts.configure_workflow import WORKFLOW,VERSION,node_map


def main():
    values=settings();p=Platform(values)
    response=p.request('/versions/'+VERSION);version=response.get('data',response)
    nodes=list(node_map(p).values())
    for node in nodes:node.pop('node_output',None)
    result={'workflow_id':WORKFLOW,'version_id':VERSION,'version_slug':version.get('slug'),
            'workflow_slug':'yhcdrf4kne4j','web_call_url':'https://platform.happyrobot.ai/deployments/yhcdrf4kne4j',
            'source':'Read-only platform snapshot','version':version,'nodes':nodes}
    text=json.dumps(result,indent=2)
    for key,value in values.items():
        if any(k in key for k in ('KEY','SECRET','TOKEN','PASSWORD')) and isinstance(value,str) and len(value)>10:
            text=text.replace(value,'[REDACTED]')
    (ROOT/'happyrobot/prototype-workflow.json').write_text(text+'\n')
    topology={'workflow_id':WORKFLOW,'version_id':VERSION,'version_slug':version.get('slug'),
              'nodes':[{k:n[k] for k in ('id','persistent_id','name')} for n in nodes]}
    (ROOT/'happyrobot/prototype-topology.json').write_text(json.dumps(topology,indent=2)+'\n')
    print('Sanitized workflow snapshot saved:',len(nodes),'nodes')


if __name__=='__main__':main()
