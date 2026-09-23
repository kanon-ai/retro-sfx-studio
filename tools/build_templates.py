"""Rebuild the original, editable factory SFX templates and audition samples."""
import base64
import copy
import hashlib
import html
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine

ROOT=engine.ROOT
DEST=ROOT/'templates'
RECIPES=[
    ('coin','コイン','アイテム取得',dict(note=84,duration=.28,attack=0,decay=.07,sustain=.65,release=.12,sequenceOn=True,sequence=[0,0,7,7,12,12,12,12])),
    ('confirm','決定音','メニューの決定・選択',dict(note=76,duration=.18,attack=.005,decay=.04,sustain=.6,release=.08,sequenceOn=True,sequence=[0,0,0,0,7,7,7,7])),
    ('jump','ジャンプ','上昇する短いジャンプ音',dict(note=45,sweep=25,curve=.65,duration=.32,attack=0,decay=.06,sustain=.7,release=.12)),
    ('laser','レーザー','下降するSFショット',dict(note=92,sweep=-46,curve=.6,duration=.38,attack=0,decay=.15,sustain=.35,release=.18,feedback=5)),
    ('impact','爆発・衝撃','低音の衝撃。PSGはノイズ、FMは変調による質感',dict(note=38,sweep=-20,curve=.5,duration=.65,attack=0,decay=.3,sustain=.12,release=.28,feedback=7)),
    ('bell','ベル','アイテム・イベント通知の余韻',dict(note=88,duration=1.2,attack=0,decay=.85,sustain=.12,release=.3)),
    ('alarm','警報','交互に音程が変わる警告音',dict(note=69,duration=1.2,attack=.008,decay=.03,sustain=.85,release=.08,sequenceOn=True,sequence=[0,7,0,7,0,7,0,7])),
    ('powerup','パワーアップ','段階的に上昇する獲得音',dict(note=60,duration=.72,attack=.005,decay=.12,sustain=.7,release=.2,sequenceOn=True,sequence=[0,4,7,12,16,19,24,24])),
]

def make_patch(chip,slug,title,settings):
    p=copy.deepcopy(engine.DEFAULT)
    p.update(name=f'{chip} / {title}',chip=chip,mode='FM',sweep=0,feedback=0,algorithm=4,
             vibrato=0,level=.8,tail=.3,sequenceOn=False,sequence=[0]*8)
    p.update(settings)
    for i,op in enumerate(p['operators']):
        op.update(mul=1,tl=36 if i in (0,2) else 10,dt=0,ar=31,dr=0,sr=0,sl=0,rr=12,wave=0)
    if chip=='PSG':
        if slug=='impact':p.update(tone=False,noise=True,noisePeriod=2,noiseEnd=31)
        if slug=='bell':p.update(vibrato=.1,speed=7)
    elif chip=='OPLL':
        p['instrument']={'coin':0,'confirm':10,'jump':0,'laser':0,'impact':0,'bell':12,'alarm':6,'powerup':0}[slug]
        for op in p['operators']:op.update(ar=15,dr=0,sl=0,rr=10)
        p['operators'][0].update(mul=2,tl=32)
        p['operators'][1].update(mul=1,tl=0)
        if slug=='coin':p['operators'][0].update(mul=3,tl=38)
        if slug=='laser':p['operators'][0].update(mul=3,tl=18)
        if slug=='impact':
            p['operators'][0].update(mul=15,tl=0,wave=1)
            p['operators'][1].update(mul=1,wave=1)
    else:
        if slug in ('coin','bell'):
            p['operators'][0].update(mul=7 if slug=='bell' else 3,tl=32)
            p['operators'][2].update(mul=11 if slug=='bell' else 2,tl=42)
        elif slug=='laser':p.update(algorithm=0);p['operators'][0].update(mul=3,tl=18)
        elif slug=='impact':
            p.update(algorithm=0)
            for op,mul,tl in zip(p['operators'],[15,7,3,1],[2,12,18,0]):op.update(mul=mul,tl=tl)
        elif slug=='powerup':p['operators'][2].update(mul=2,tl=30)
        if chip=='OPM' and slug in ('bell','powerup'):p['operators'][2]['dt']=1
    return engine.validate(p)

def main():
    DEST.mkdir(exist_ok=True);(DEST/'patches').mkdir(exist_ok=True);(DEST/'audio').mkdir(exist_ok=True)
    entries=[]
    for chip in engine.CHIPS:
        for slug,title,description,settings in RECIPES:
            p=make_patch(chip,slug,title,settings);ident=f'{chip.lower()}-{slug}'
            patch_path=f'patches/{ident}.json';audio_path=f'audio/{ident}.wav'
            (DEST/patch_path).write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            audio=engine.render(p);(DEST/audio_path).write_bytes(audio)
            entries.append(dict(id=ident,chip=chip,category=slug,title=title,description=description,
                                patchFile=patch_path,audioFile=audio_path,audioSha256=hashlib.sha256(audio).hexdigest(),patch=p))
    (DEST/'catalog.json').write_text(json.dumps(dict(version=1,templates=entries),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 効果音テンプレート / Sound templates','',
           '各音源8種、合計40種のオリジナル効果音テンプレートです。既存12プリセットに続くPROGRAM 13〜52（MCP index 12〜51）として利用できます。','',
           '- GUI：PROGRAMから音源名付きの音色を選択。または「読込」でpatches内のJSONを開きます。',
           '- MCP：list_presets → get_preset → パラメーター調整 → export_sound。',
           '- 試聴：ZIPを全て展開し、preview.htmlをブラウザーで開いてください。',
           '- WAVとJSONは同じ設定から生成。catalog.jsonに説明・設定・WAVのSHA-256を記録しています。',
           '- プリセットは音作りの出発点です。長さ、基準音、包絡、FMオペレーターを自由に調整できます。',
           '- PSGの「ベル」は矩形波による通知音、FMの「爆発・衝撃」は変調による音です。専用PCM音源ではありません。',
           '- チップに応じた音程・包絡の量子化があります。実機の回路差は再現せず、実機未検証です。',
           '- 本プロジェクト独自のパッチと音声はCC0-1.0で提供します。商用・非商用で利用・改変でき、クレジットは必須ではありません。',
           '  詳細は[LICENSE](LICENSE)。本ツールのコードは引き続きMIT、第三者コードは各ライセンスです。','',
           '| PROGRAM / MCP index | 音源 | 音色・用途 | パッチ | 試聴 |','|---|---|---|---|---|']
    cards=[]
    embedded={}
    for i,e in enumerate(entries,12):
        lines.append(f"| {i+1:02d} / {i} | {e['chip']} | {e['title']}：{e['description']} | [JSON]({e['patchFile']}) | [WAV]({e['audioFile']}) |")
        embedded[e['id']]=base64.b64encode((DEST/e['audioFile']).read_bytes()).decode('ascii')
        cards.append(f'<article data-chip="{e["chip"]}"><span>{e["chip"]} · P{i+1:02d}</span><h2>{html.escape(e["title"])}</h2><p>{html.escape(e["description"])}</p><div class="player"><button class="audition" data-sample="{e["id"]}">▶ 試聴</button><small>{e["patch"]["duration"]+e["patch"]["tail"]:.2f} s</small></div><a href="{e["patchFile"]}" download>編集用JSON</a> · <a href="{e["audioFile"]}" download>WAV</a></article>')
    (DEST/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    preview='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RETRO / SFX · 音色テンプレート</title><style>
body{margin:0;background:#1c2325;color:#dbe4cc;font:14px "Segoe UI",sans-serif;padding:32px}main{max-width:1200px;margin:auto}h1{font-size:30px}h1 span{color:#bcdb80}p{color:#a9b69f;line-height:1.7}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}button,a{color:#c5e18e}button{background:#303b38;border:1px solid #718760;border-radius:5px;padding:10px 20px;cursor:pointer}button[aria-pressed=true]{background:#bfd68b;color:#24301b}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:18px}article{padding:20px;background:#293233;border:1px solid #4a594a;border-radius:8px}article>span{font-size:11px;color:#b8d287}article p{min-height:48px;font-size:12px}.player{display:flex;align-items:center;gap:16px;margin:16px 0}.player small{color:#b9c9a6}a{font-size:12px}[hidden]{display:none!important}</style><main><h1>RETRO <span>/</span> SFX <small>音色テンプレート</small></h1><p>5音源 × 8種類のサンプル。再生して選び、JSONをアプリに読み込んで編集できます。<br>このページは全ファイルを展開すればオフラインで試聴できます。パッチ・音声はCC0-1.0。</p><nav>'''
    preview+=''.join(f'<button data-filter="{x}" aria-pressed="{str(x=="ALL").lower()}">{x}</button>' for x in ['ALL',*engine.CHIPS])+'</nav><div class="grid">'+''.join(cards)+'</div></main>'
    preview+='<script id="samples" type="application/json">'+json.dumps(embedded)+'</script>'
    preview+='''<script>
+const samples=JSON.parse(document.getElementById('samples').textContent);let ctx,source,active,serial=0;
+function stop(){serial++;if(source){source.onended=null;try{source.stop();}catch{}source=null;}if(active){active.textContent='▶ 試聴';active=null;}}
+document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{stop();document.querySelectorAll('nav button').forEach(x=>x.setAttribute('aria-pressed',x===b));document.querySelectorAll('article').forEach(a=>{a.hidden=b.dataset.filter!=='ALL'&&a.dataset.chip!==b.dataset.filter;});});
+document.querySelectorAll('.audition').forEach(b=>b.onclick=async()=>{if(active===b){stop();return;}stop();const ticket=serial;active=b;b.textContent='準備中…';try{ctx??=new AudioContext();await ctx.resume();const bytes=Uint8Array.from(atob(samples[b.dataset.sample]),c=>c.charCodeAt(0));const buffer=await ctx.decodeAudioData(bytes.buffer);if(ticket!==serial)return;source=ctx.createBufferSource();source.buffer=buffer;const gain=ctx.createGain();gain.gain.value=.65;source.connect(gain);gain.connect(ctx.destination);b.textContent='■ 停止';source.onended=()=>{if(active===b){b.textContent='▶ 試聴';active=null;source=null;}};source.start();}catch(e){if(ticket===serial){b.textContent='再生失敗：WAVを開いてください';active=null;}}});
+</script></html>'''.replace('\n+','\n')
    (DEST/'preview.html').write_text(preview,encoding='utf-8')
    print('Built',len(entries),'templates and WAV samples')

if __name__=='__main__':main()
