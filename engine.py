"""Register-based, single-voice SFX authoring. No external Python packages."""
import copy
import io
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else ROOT
RATE = 44100
CHIPS = {
    'PSG': dict(kind=0, clock=1789773, offset=0x74, command=0xA0, label='MSX · PSG / YM2149'),
    'OPLL': dict(kind=1, clock=3579545, offset=0x10, command=0x51, label='MSX · OPLL / YM2413'),
    'OPN': dict(kind=2, clock=3993600, offset=0x44, command=0x55, label='PC-9801 · OPN / YM2203'),
    'OPNA': dict(kind=3, clock=7987200, offset=0x48, command=0x56, label='PC-9801 · OPNA / YM2608'),
    'OPM': dict(kind=4, clock=4000000, offset=0x30, command=0x54, label='X68000 · OPM / YM2151'),
}
OP_DEFAULT = dict(mul=1, tl=22, dt=0, ar=31, dr=8, sr=0, sl=5, rr=10, wave=0)
DEFAULT = dict(version=1, name='Neon laser', chip='OPNA', mode='FM', duration=0.6,
               tail=0.35, note=76, sweep=-32, curve=1.0, vibrato=0, speed=6,
               attack=0.005, decay=0.18, sustain=0.35, release=0.18,
               level=0.8, algorithm=0, feedback=4, instrument=0,
               tone=True, noise=False, noisePeriod=12, noiseEnd=28,
               sequence=[0]*8, sequenceOn=False, pan='C',
               operators=[dict(OP_DEFAULT, mul=2, tl=28), dict(OP_DEFAULT, tl=38),
                          dict(OP_DEFAULT, tl=32), dict(OP_DEFAULT, tl=0)])
RANGES = dict(duration=(.06,5), tail=(.05,2), note=(12,108), sweep=(-72,72), curve=(.2,4),
              vibrato=(0,12), speed=(.1,30), attack=(0,2), decay=(0,2), sustain=(0,1),
              release=(0,2), level=(0,1), algorithm=(0,7), feedback=(0,7), instrument=(0,15),
              noisePeriod=(1,31), noiseEnd=(1,31))
INTS = {'note','algorithm','feedback','instrument','noisePeriod','noiseEnd'}
OP_RANGES = dict(mul=(0,15),tl=(0,127),dt=(0,7),ar=(0,31),dr=(0,31),sr=(0,31),sl=(0,15),rr=(0,15),wave=(0,1))

def number(v, low, high, integer=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:
        raise ValueError(f'数値は {low} ～ {high} の範囲で指定してください。')
    if integer and int(v)!=v: raise ValueError('整数を指定してください。')
    return int(v) if integer else float(v)

def validate(data):
    if not isinstance(data,dict): raise ValueError('パッチはJSONオブジェクトで指定してください。')
    if data.get('version',1)!=1: raise ValueError('未対応のパッチバージョンです。')
    p=copy.deepcopy(DEFAULT)
    if any(k not in p for k in data): raise ValueError('不明なパッチ項目があります。')
    p.update(data)
    if p['chip'] not in CHIPS or p['mode'] not in ('FM','SSG'): raise ValueError('音源の指定が不正です。')
    if not isinstance(p['name'],str) or not 1<=len(p['name'])<=64: raise ValueError('名前は1～64文字にしてください。')
    if p['pan'] not in ('L','C','R'): raise ValueError('PANの指定が不正です。')
    for k,(lo,hi) in RANGES.items(): p[k]=number(p[k],lo,hi,k in INTS)
    for k in ('tone','noise','sequenceOn'):
        if not isinstance(p[k],bool): raise ValueError(f'{k} は真偽値を指定してください。')
    if not isinstance(p['sequence'],list) or len(p['sequence'])!=8: raise ValueError('シーケンスは8ステップです。')
    p['sequence']=[number(v,-24,24,True) for v in p['sequence']]
    if not isinstance(p['operators'],list) or len(p['operators'])!=4: raise ValueError('オペレーターは4個必要です。')
    for i,op in enumerate(p['operators']):
        if not isinstance(op,dict) or any(k not in OP_RANGES for k in op): raise ValueError('オペレーターの設定が不正です。')
        op=dict(OP_DEFAULT,**op)
        p['operators'][i]={k:number(op[k],*bounds,True) for k,bounds in OP_RANGES.items()}
    return p

def envelope(p,t):
    # A/D are fitted to the gate when necessary; R occupies the end of the gate.
    d=p['duration']; r=min(p['release'],d); gate=d-r
    a=p['attack']; decay=p['decay']
    scale=min(1,gate/max(a+decay,1e-9)); a*=scale; decay*=scale
    def held(x):
        if a>0 and x<a: return x/a
        if decay>0 and x<a+decay: return 1-(1-p['sustain'])*(x-a)/decay
        return p['sustain']
    if t>=d: return 0
    if r and t>=gate: return held(gate)*max(0,(d-t)/r)
    return held(t)

def pitch(p,t):
    x=min(1,t/p['duration'])
    step=p['sequence'][min(7,int(x*8))] if p['sequenceOn'] else 0
    return p['note']+p['sweep']*x**p['curve']+p['vibrato']*math.sin(t*p['speed']*2*math.pi)+step

def is_ssg(p): return p['chip']=='PSG' or (p['chip'] in ('OPN','OPNA') and p['mode']=='SSG')

def compile_patch(data):
    p=validate(data); chip=p['chip']; info=CHIPS[chip]; clock=info['clock']; events=[]; old={}
    def put(t,reg,value,force=False):
        value=int(value)&255
        if force or old.get(reg)!=value:
            events.append((round(t*RATE),reg,value)); old[reg]=value
    ssg=is_ssg(p)
    ops=p['operators']; alg=p['algorithm']; pan={'L':0x80,'C':0xc0,'R':0x40}[p['pan']]
    if chip=='OPM': pan={'L':0x40,'C':0xc0,'R':0x80}[p['pan']]
    offsets=[0,8,4,12] if chip!='OPM' else [0,16,8,24]
    carriers=[[3],[3],[3],[3],[1,3],[1,2,3],[1,2,3],[0,1,2,3]][alg]
    if chip in ('OPN','OPNA'):
        put(0,7,0x3f); put(0,8,0); put(0,9,0); put(0,10,0); put(0,0x27,0)
        if chip=='OPNA': put(0,0x29,0x80)
    if ssg:
        put(0,7,0x3f ^ (1 if p['tone'] else 0) ^ (8 if p['noise'] else 0)); put(0,9,0); put(0,10,0)
    elif chip=='OPLL':
        # User instrument: M and C, sustain enabled; software envelope controls C volume.
        for i in range(2): put(0,i,0x20|ops[i]['mul'])
        put(0,2,min(63,ops[0]['tl']))
        put(0,3,p['feedback']|(ops[0]['wave']<<3)|(ops[1]['wave']<<4))
        for i in range(2):
            put(0,4+i,(min(15,ops[i]['ar'])<<4)|min(15,ops[i]['dr']))
            put(0,6+i,(ops[i]['sl']<<4)|ops[i]['rr'])
    else:
        put(0,0x20 if chip=='OPM' else 0xb0,(pan if chip=='OPM' else 0)|(p['feedback']<<3)|alg)
        if chip=='OPNA': put(0,0xb4,pan)
        for i,op in enumerate(ops):
            off=offsets[i]
            if chip=='OPM':
                for base,value in [(0x40,op['dt']*16+op['mul']),(0x60,op['tl']),(0x80,op['ar']),(0xa0,op['dr']),(0xc0,op['sr']),(0xe0,op['sl']*16+op['rr'])]: put(0,base+off,value)
            else:
                for base,value in [(0x30,op['dt']*16+op['mul']),(0x40,op['tl']),(0x50,op['ar']),(0x60,op['dr']),(0x70,op['sr']),(0x80,op['sl']*16+op['rr']),(0x90,0)]: put(0,base+off,value)
    # 240 Hz parameter automation; exported times use the VGM 44.1 kHz timebase.
    high=0
    for frame in range(math.ceil(p['duration']*240)):
        t=frame/240; freq=440*2**((pitch(p,t)-69)/12); amp=p['level']*envelope(p,t)
        if ssg:
            ssgclock=clock if chip=='PSG' else clock/(2 if chip=='OPN' else 4)
            period=max(1,min(4095,round(ssgclock/(16*freq))))
            put(t,0,period&255); put(t,1,period>>8)
            put(t,6,round(p['noisePeriod']+(p['noiseEnd']-p['noisePeriod'])*t/p['duration']))
            volume=0 if amp<=.002 else max(0,min(15,round(15+math.log2(amp)*2)))
            put(t,8,volume)
        elif chip=='OPLL':
            block=0; fnum=freq*72*2**19/clock
            while fnum>511 and block<7: block+=1; fnum/=2
            fnum=max(0,min(511,round(fnum))); high=(block<<1)|(fnum>>8)
            put(t,0x10,fnum&255); put(t,0x20,high|(0x10 if p['level']>0 else 0))
            att=15 if amp<=.001 else min(15,round(-20*math.log10(amp)/3))
            put(t,0x30,(p['instrument']<<4)|att)
        else:
            if chip=='OPM':
                n=69+12*math.log2(freq/440)-12*math.log2(clock/3579545)-13
                n=max(0,min(95.984375,n)); whole=int(n); octave=whole//12; semitone=whole%12
                code=[0,1,2,4,5,6,8,9,10,12,13,14][semitone]
                put(t,0x28,(octave<<4)|code); put(t,0x30,int((n-whole)*64)<<2)
            else:
                block=0; fnum=freq*(144 if chip=='OPNA' else 72)*2**21/clock
                while fnum>2047 and block<7: block+=1; fnum/=2
                fnum=max(0,min(2047,round(fnum)))
                put(t,0xa4,(block<<3)|(fnum>>8)); put(t,0xa0,fnum&255,True)
            att=127 if amp<=.0001 else round(-20*math.log10(amp)/.75)
            for i in carriers: put(t,(0x60 if chip=='OPM' else 0x40)+offsets[i],min(127,ops[i]['tl']+att))
            if frame==0 and p['level']>0: put(0,0x08 if chip=='OPM' else 0x28,0x78 if chip=='OPM' else 0xf0,True)
    end=p['duration']
    if ssg: put(end,8,0)
    elif chip=='OPLL': put(end,0x20,high); put(end,0x30,(p['instrument']<<4)|15)
    else:
        put(end,0x08 if chip=='OPM' else 0x28,0,True)
        for i in carriers: put(end,(0x60 if chip=='OPM' else 0x40)+offsets[i],127)
    frames=round((end+p['tail'])*RATE)
    return p,events,frames

def vgm(data):
    p,events,frames=compile_patch(data); info=CHIPS[p['chip']]; body=bytearray(); previous=0
    def wait(n):
        while n:
            part=min(n,65535); body.extend(struct.pack('<BH',0x61,part)); n-=part
    for time,reg,value in events:
        wait(time-previous); previous=time
        body.extend((info['command']+(1 if reg>255 and p['chip']=='OPNA' else 0),reg&255,value))
    wait(frames-previous); body.append(0x66)
    header=bytearray(256); header[:4]=b'Vgm '
    for offset,value in [(4,256+len(body)-4),(8,0x171),(0x18,frames),(0x34,256-0x34),(info['offset'],info['clock'])]: struct.pack_into('<I',header,offset,value)
    if p['chip']=='PSG': header[0x78]=0x10 # YM2149
    return bytes(header+body)

def register_json(data):
    p,events,frames=compile_patch(data)
    return dict(format='retro-sfx-registers-v1',chip=p['chip'],clock=CHIPS[p['chip']]['clock'],
                timebase=RATE,totalSamples=frames,channel=0,events=[dict(sample=t,register=r,value=v) for t,r,v in events])

def c_header(data):
    p,events,frames=compile_patch(data)
    lines=['/* Retro SFX Studio - channel 0. Wait at 44100 Hz timebase before each write.',
           ' * Chip: '+p['chip']+'; clock: '+str(CHIPS[p['chip']]['clock'])+' Hz.',
           ' * Apply hardware busy waits; preserve shared mixer/IO bits when integrating.',
           ' * Standalone data: an engine adapter is required. */', '#pragma once','#include <stdint.h>',
           'typedef struct { uint32_t wait_samples; uint16_t reg; uint8_t value; } retro_sfx_event;',
           'static const retro_sfx_event retro_sfx[] = {']
    previous=0
    for t,r,v in events: lines.append(f'    {{ {t-previous}, 0x{r:03X}, 0x{v:02X} }},'); previous=t
    lines+=['};',f'static const uint32_t retro_sfx_count = {len(events)};',f'static const uint32_t retro_sfx_tail_samples = {frames-previous};','']
    return '\n'.join(lines).encode('utf-8')

def render(data):
    p,events,frames=compile_patch(data); info=CHIPS[p['chip']]
    candidates=[ROOT/'bin/retro_render.exe',ROOT/'build-vs/Release/retro_render.exe',ROOT/'build/Release/retro_render.exe',ROOT/'build/retro_render']
    exe=next((f for f in candidates if f.is_file()),None)
    if not exe: raise RuntimeError('音源エンジンがありません。build.ps1 を実行してください。')
    with tempfile.TemporaryDirectory(prefix='retro-sfx-') as tmp:
        source=Path(tmp)/'events.txt'; dest=Path(tmp)/'audio.wav'
        source.write_text(f"{info['kind']} {info['clock']} {frames} {len(events)}\n"+'\n'.join(f'{t} {r} {v}' for t,r,v in events),encoding='ascii')
        subprocess.run([str(exe),str(source),str(dest)],check=True,capture_output=True,timeout=20,
                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return dest.read_bytes()

def presets():
    bank=[]
    definitions=[('Neon laser',dict()),('Crystal coin',dict(chip='PSG',note=84,sweep=0,duration=.3,attack=0,decay=.1,sustain=.7,release=.1,sequenceOn=True,sequence=[0,0,7,7,12,12,12,12])),
        ('Arcade jump',dict(chip='PSG',note=48,sweep=24,duration=.35,curve=.7,attack=0,decay=.1,sustain=.6,release=.12)),
        ('Noise burst',dict(chip='PSG',tone=False,noise=True,noisePeriod=3,noiseEnd=31,duration=.7,attack=0,decay=.4,sustain=.2,release=.25)),
        ('Space alarm',dict(chip='OPLL',instrument=6,note=69,sweep=0,vibrato=7,speed=4,duration=1.5,attack=.01,decay=0,sustain=.8,release=.1)),
        ('Glass bell',dict(chip='OPM',algorithm=4,note=84,sweep=0,duration=1.4,attack=0,decay=1.1,sustain=.05,release=.25,feedback=1)),
        ('Metal impact',dict(chip='OPN',note=42,sweep=-12,duration=.45,feedback=7,attack=0,decay=.3,sustain=.05,release=.1)),
        ('Power up',dict(chip='OPNA',algorithm=4,note=60,sweep=12,duration=.8,attack=.01,decay=.15,sustain=.7,release=.2,sequenceOn=True,sequence=[0,4,7,12,0,4,7,12])),
        ('Soft confirm',dict(chip='OPLL',instrument=10,note=81,sweep=0,duration=.25,attack=.005,decay=.1,sustain=.3,release=.1)),
        ('Engine fall',dict(chip='OPM',note=48,sweep=-24,duration=1.2,feedback=7,vibrato=1.2,speed=20,attack=.01,decay=.3,sustain=.8,release=.4)),
        ('SSG click',dict(chip='OPNA',mode='SSG',note=96,sweep=-12,duration=.09,attack=0,decay=.03,sustain=.1,release=.04)),
        ('Pure tone',dict(chip='OPN',algorithm=7,note=69,sweep=0,feedback=0,duration=.8,attack=.01,decay=0,sustain=1,release=.1))]
    for name,change in definitions:
        p=copy.deepcopy(DEFAULT); p.update(change); p['name']=name
        if name=='Pure tone':
            for i in range(3): p['operators'][i]['tl']=127
            p['operators'][3].update(ar=31,dr=0,sr=0,tl=0)
        if name=='Glass bell': p['operators'][0].update(mul=7,tl=38); p['operators'][1].update(mul=1,tl=8)
        bank.append(validate(p))
    return bank
