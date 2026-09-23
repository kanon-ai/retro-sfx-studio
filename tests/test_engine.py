import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import wave
import zipfile
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine
import handoff

def samples(p):
    raw=engine.render(p)
    with wave.open(io.BytesIO(raw)) as wav:
        assert wav.getframerate()==44100 and wav.getnchannels()==2 and wav.getsampwidth()==2
        return array('h',wav.readframes(wav.getnframes())),raw

def pure(chip,mode='FM'):
    p=copy.deepcopy(engine.presets()[-1]);p.update(chip=chip,mode=mode,attack=0,decay=0,release=.1,sustain=1,level=.6)
    if chip=='OPLL':
        p['instrument']=0
        for i in range(2):p['operators'][i].update(mul=1,tl=63 if i==0 else 0,ar=15,dr=0,sr=0,sl=0,rr=8)
    return p

class AudioTests(unittest.TestCase):
    def test_presets_nonzero_repeatable(self):
        for p in engine.presets():
            with self.subTest(p=p['name']):
                a,raw=samples(p);self.assertGreater(max(abs(v) for v in a),30);self.assertEqual(raw,engine.render(p))
                self.assertEqual(len(a)//2,round((p['duration']+p['tail'])*44100))
                self.assertLess(max(abs(v) for v in a[-2000:]),50)

    def test_pitch_all_chips(self):
        for chip,mode in [(c,'FM') for c in engine.CHIPS]+[('OPN','SSG'),('OPNA','SSG')]:
            with self.subTest(chip=chip,mode=mode):
                a,_=samples(pure(chip,mode));left=a[2*4410:2*22050:2]
                crosses=[i for i in range(1,len(left)) if left[i-1]<=0<left[i]]
                freq=(len(crosses)-1)*44100/(crosses[-1]-crosses[0])
                print(f'Pitch {chip}/{mode}: {freq:.3f} Hz')
                self.assertAlmostEqual(freq,440,delta=4)

    def test_pan_and_silence(self):
        for chip in ('OPNA','OPM'):
            for side in ('L','R'):
                p=pure(chip);p['pan']=side;a,_=samples(p)
                audible=a[0::2] if side=='L' else a[1::2];muted=a[1::2] if side=='L' else a[0::2]
                self.assertGreater(max(abs(v) for v in audible),100);self.assertEqual(max(abs(v) for v in muted),0)
        for chip in engine.CHIPS:
            p=pure(chip);p['level']=0;a,_=samples(p)
            # Hardware FM TL maximum is extreme attenuation, not a mathematical mute.
            self.assertLessEqual(max(abs(v) for v in a),8)

    def test_vgm_roundtrip(self):
        for p in engine.presets():
            v=engine.vgm(p);_,events,frames=engine.compile_patch(p)
            self.assertEqual(v[:4],b'Vgm ');self.assertEqual(struct.unpack_from('<I',v,4)[0],len(v)-4)
            self.assertEqual(struct.unpack_from('<I',v,engine.CHIPS[p['chip']]['offset'])[0],engine.CHIPS[p['chip']]['clock'])
            pos=0x34+struct.unpack_from('<I',v,0x34)[0];t=0;parsed=[]
            while v[pos]!=0x66:
                op=v[pos];pos+=1
                if op==0x61:t+=struct.unpack_from('<H',v,pos)[0];pos+=2
                else:
                    self.assertEqual(op,engine.CHIPS[p['chip']]['command']);parsed.append((t,v[pos],v[pos+1]));pos+=2
            self.assertEqual(parsed,events);self.assertEqual(t,frames);self.assertEqual(pos+1,len(v))

    def test_bundle(self):
        p=engine.presets()[1]
        with zipfile.ZipFile(io.BytesIO(handoff.bundle(p))) as z:
            self.assertEqual(set(z.namelist()),{'patch.json','sound.wav','sound.vgm','sound.h','registers.json','AI_HANDOFF.md','manifest.json'})
            manifest=json.loads(z.read('manifest.json'))
            for name,digest in manifest['files'].items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
            self.assertEqual(engine.validate(json.loads(z.read('patch.json'))),p)
            self.assertEqual(z.read('sound.wav'),engine.render(p))

    def test_invalid_inputs(self):
        for value in [-1,float('nan'),float('inf'),'1',None,True]:
            with self.assertRaises(ValueError):engine.validate({'duration':value})
        for bad in [{'chip':'OTHER'},{'sequence':[1]},{'version':2},{'operators':[]},{'unknown':1}]:
            with self.assertRaises(ValueError):engine.validate(bad)

    def test_mcp_process(self):
        messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_preset','arguments':{'index':1}}},
            {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'validate_patch','arguments':{'patch':{'duration':-1}}}},
            {'jsonrpc':'2.0','id':5,'method':'tools/call','params':{'name':'export_sound','arguments':{'patch':engine.presets()[1]}}}]
        proc=subprocess.run([sys.executable,str(engine.ROOT/'mcp_server.py')],input=('\n'.join(json.dumps(m) for m in messages)+'\n').encode(),capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stderr);replies=[json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(replies),5);self.assertEqual(replies[0]['result']['protocolVersion'],'2025-11-25');self.assertEqual(len(replies[1]['result']['tools']),6)
        self.assertTrue(replies[3]['result']['isError']);self.assertFalse(replies[4]['result']['isError'])
        data=json.loads(replies[4]['result']['content'][0]['text']);self.assertTrue(Path(data['files']['ai-package.zip']).is_file())

if __name__=='__main__': unittest.main(verbosity=2)
