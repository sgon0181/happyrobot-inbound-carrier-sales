"""Production Twin SQL transport, with no credential-bearing error output."""
import asyncio
import json
import time
import urllib.error
import urllib.request


def literal(value):
    return 'NULL' if value is None else "'" + str(value).replace("'", "''") + "'"


class PlatformError(RuntimeError):
    def __init__(self, code,detail=None):
        self.code,self.detail = code,detail
        super().__init__('Platform request failed: ' + str(code))


class Platform:
    base = 'https://platform.happyrobot.ai/api/v2'

    def __init__(self, values):
        self.values, self.key = values, values['HAPPYROBOT_API_KEY']
        self.latencies = []
        self.notification_lock = asyncio.Lock()

    def request(self, path, body=None, method=None):
        request = urllib.request.Request(self.base + path,
            data=json.dumps(body).encode() if body is not None else None, method=method,
            headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json',
                     'x-organization-id':self.values.get('HAPPYROBOT_ORG_ID','01a17a99-0856-7f88-b09f-4b787e20413c'),
                     'x-twin-environment':'production'})
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            code = error.code
            try:detail=json.loads(error.read()).get('message','request rejected')
            except (ValueError,AttributeError):detail='request rejected'
            for value in self.values.values():
                if isinstance(value,str) and len(value)>7:detail=detail.replace(value,'[REDACTED]')
            error.close()
            raise PlatformError(code,detail) from None
        except (OSError, ValueError):
            raise PlatformError('unavailable') from None
        self.latencies.append(time.monotonic()-started)
        return result

    async def sql(self, sql):
        return await asyncio.to_thread(self.request, '/twin/sql', {'sql':sql})
