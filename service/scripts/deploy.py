"""Single-command deployment to the owner's explicitly approved Fly app only."""
import os
import json
from pathlib import Path
import subprocess
from service.config import ROOT

APP='codex-e2e-lab-sg-20261031'
IMAGE='registry.fly.io/'+APP+':prototype-e2e'


def main():
    endpoint=subprocess.check_output(['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'],text=True).strip()
    directory=ROOT/'secrets/docker-config';directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    config=directory/'config.json'
    if not config.exists():config.write_text('{}\n')
    data=json.loads(config.read_text())
    vendor=Path('/Applications/Docker.app/Contents/Resources/cli-plugins')
    if vendor.exists():
        data['cliPluginsExtraDirs']=[str(vendor)]
        config.write_text(json.dumps(data))
    config.chmod(0o600)
    env=dict(os.environ,DOCKER_CONFIG=str(directory),DOCKER_HOST=endpoint)
    commands=[['docker','build','--platform','linux/amd64','-t',IMAGE,'.'],
              ['fly','auth','docker'],['docker','push',IMAGE],
              ['fly','deploy','--config','fly.toml','--image',IMAGE,'--ha=false']]
    for command in commands:
        subprocess.run(command,cwd=ROOT,env=env,check=True)
        config.chmod(0o600)


if __name__=='__main__':main()
