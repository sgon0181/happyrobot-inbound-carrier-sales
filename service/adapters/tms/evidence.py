"""Private fsynced receipt journal, independent of Twin and socket cleanup.

Container files are ephemeral. Restricted receipt fallback logs and Twin remain
the remote evidence sources; export private files before replacing a machine.
"""
import base64
import json
import os
from pathlib import Path
import stat
import uuid


class ReceiptJournal:
    def __init__(self,directory):self.directory=Path(directory)
    def path(self,identity):return self.directory/(uuid.UUID(identity).hex+'.jsonl')
    def begin(self,context):
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        info=self.directory.stat()
        if info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)&0o077:raise OSError('Private capture required')
        fd=os.open(self.path(context['intent_id']),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as file:
            file.write((json.dumps({'context':context})+'\n').encode());file.flush();os.fsync(file.fileno())
    def received(self,identity,chunk):
        with self.path(identity).open('ab') as file:
            file.write((json.dumps({'bytes_b64':base64.b64encode(chunk).decode()})+'\n').encode())
            file.flush();os.fsync(file.fileno())
    def read(self,context):
        try:
            path=self.path(context['intent_id']);info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_size>100000 or stat.S_IMODE(info.st_mode)&0o077:return None
            rows=[]
            for line in path.read_bytes().splitlines(keepends=True):
                if not line.endswith(b'\n'):break
                try:row=json.loads(line)
                except ValueError:break
                if not isinstance(row,dict):break
                rows.append(row)
            if not rows or rows[0].get('context')!=context:return None
            return b''.join(base64.b64decode(row['bytes_b64'],validate=True) for row in rows[1:] if 'bytes_b64' in row)
        except (OSError,ValueError,TypeError,KeyError):return None
