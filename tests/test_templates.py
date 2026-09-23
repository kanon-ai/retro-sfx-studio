import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import wave
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine
import mcp_server

class TemplateTests(unittest.TestCase):
    def test_original_presets_unchanged(self):
        baseline=json.loads((Path(__file__).parent/'fixtures/original-presets-v1.json').read_text(encoding='utf-8'))
        self.assertEqual(engine.presets()[:12],baseline['patches'])
        self.assertEqual([hashlib.sha256(engine.render(p)).hexdigest() for p in engine.presets()[:12]],baseline['audioSha256'])

    def test_catalog_and_samples(self):
        root=engine.ROOT/'templates';entries=json.loads((root/'catalog.json').read_text(encoding='utf-8'))['templates']
        self.assertEqual(len(entries),40)
        self.assertEqual(len({e['id'] for e in entries}),40)
        for chip in engine.CHIPS:
            selected=[e for e in entries if e['chip']==chip]
            self.assertEqual(len(selected),8)
            self.assertEqual(len({e['audioSha256'] for e in selected}),8)
        for e in entries:
            with self.subTest(template=e['id']):
                p=json.loads((root/e['patchFile']).read_text(encoding='utf-8'))
                self.assertEqual(p,engine.validate(e['patch']))
                blob=(root/e['audioFile']).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(),e['audioSha256'])
                self.assertEqual(blob,engine.render(p))
                with wave.open(io.BytesIO(blob)) as wav:
                    self.assertEqual(wav.getframerate(),44100)
                    self.assertEqual(wav.getnchannels(),2)
                    data=array('h',wav.readframes(wav.getnframes()))
                peak=max(abs(v) for v in data)
                self.assertGreater(peak,100)
                self.assertLess(peak,32767)

    def test_mcp_template_discovery(self):
        listing=json.loads(mcp_server.call('list_presets',{})['content'][0]['text'])['presets']
        self.assertEqual(len(listing),52)
        schema=next(t for t in mcp_server.TOOLS if t['name']=='get_preset')['inputSchema']
        self.assertEqual(schema['properties']['index']['maximum'],51)
        last=json.loads(mcp_server.call('get_preset',{'index':51})['content'][0]['text'])
        self.assertEqual(last,engine.presets()[51])
        with self.assertRaises(ValueError):mcp_server.call('get_preset',{'index':52})

if __name__=='__main__':unittest.main()
