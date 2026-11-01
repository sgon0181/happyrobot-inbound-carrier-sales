"""Switch the single approved Fly Machine between warm QA and budget idle."""
import argparse
import json
from pathlib import Path
import subprocess
from service.config import ROOT
from service.scripts.deploy import APP,IMAGE


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['warm','idle'])
    args=parser.parse_args()
    machines=json.loads(subprocess.check_output(['fly','machine','list','--app',APP,'--json'],text=True))
    if len(machines)!=1:raise SystemExit('Expected exactly one existing Machine. Review instead of creating extras.')
    source=(ROOT/'fly.toml').read_text()
    if source.count('min_machines_running = 0')!=1:raise SystemExit('Unexpected base config. Nothing changed.')
    if args.mode=='warm':source=source.replace('min_machines_running = 0','min_machines_running = 1')
    path=ROOT/'secrets/fly-session.toml';path.write_text(source);path.chmod(0o600)
    subprocess.run(['fly','deploy','--config',str(path),'--image',IMAGE,'--ha=false'],cwd=ROOT,check=True)
    if args.mode=='warm':
        current=json.loads(subprocess.check_output(['fly','machine','list','--app',APP,'--json'],text=True))
        if len(current)!=1 or current[0]['id']!=machines[0]['id']:
            raise SystemExit('Machine identity changed. Review instead of starting anything.')
        if current[0]['state'] in ('stopped','suspended'):
            subprocess.run(['fly','machine','start',current[0]['id'],'--app',APP],check=True)
        elif current[0]['state']!='started':
            raise SystemExit('Machine is not ready. Review its state before testing.')
    print('Single prototype Machine configured:',args.mode)
    if args.mode=='warm':print('Restore idle mode when this QA session finishes. Fly has no hard spending cap.')


if __name__=='__main__':main()
