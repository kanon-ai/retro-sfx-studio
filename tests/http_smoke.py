"""Integration check against a running GUI server (default port 7911)."""
import hashlib
import io
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request,urlopen
import wave
import zipfile

base='http://127.0.0.1:7911'
def post(route,p,origin=base):
    request=Request(base+'/api/'+route,data=json.dumps(p).encode(),headers={'Content-Type':'application/json','Origin':origin})
    with urlopen(request,timeout=30) as response:return response.read()
with urlopen(base+'/api/info') as response:info=json.load(response)
for chip in info['chips']:
    p=dict(info['default'],chip=chip)
    raw=post('render',p)
    with wave.open(io.BytesIO(raw)) as wav:assert wav.getnframes()==41895
    assert post('vgm',p).startswith(b'Vgm ')
    assert json.loads(post('registers',p))['chip']==chip
    print('HTTP render + VGM + registers:',chip)
bundle=post('bundle',info['presets'][1])
with zipfile.ZipFile(io.BytesIO(bundle)) as z:
    manifest=json.loads(z.read('manifest.json'))
    for name,digest in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
assert 'AI引き渡し' in post('handoff',info['default']).decode()
assert b'retro_sfx_event' in post('header',info['default'])
assert json.loads(post('validate',info['default']))==info['default']
for p,origin,expected in [({'duration':-1},base,400),({},'https://example.invalid',403)]:
    try:post('render',p,origin);raise AssertionError('Unexpected acceptance')
    except HTTPError as e:assert e.code==expected
print('HTTP ZIP/hash, handoff, C header, patch roundtrip, invalid input and Origin checks PASSED')
