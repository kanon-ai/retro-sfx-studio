"""MCP stdio JSON-RPC server. stdout is reserved exclusively for the protocol."""
import argparse
import datetime
import json
from pathlib import Path
import sys
import uuid
import engine
import handoff

OUTPUT=engine.DATA_ROOT/'outputs'
SUPPORTED=['2025-11-25','2025-06-18','2025-03-26','2024-11-05']
PATCH_SCHEMA={'type':'object','description':'Complete or partial patch. Omitted fields use defaults. Use get_preset to obtain a complete editable patch.',
              'properties':{'name':{'type':'string','maxLength':64},'chip':{'type':'string','enum':list(engine.CHIPS)},'mode':{'type':'string','enum':['FM','SSG']}}}
for key,(low,high) in engine.RANGES.items(): PATCH_SCHEMA['properties'][key]={'type':'integer' if key in engine.INTS else 'number','minimum':low,'maximum':high}
for key in ('tone','noise','sequenceOn'): PATCH_SCHEMA['properties'][key]={'type':'boolean'}
PATCH_SCHEMA['properties'].update(version={'type':'integer','const':1},pan={'type':'string','enum':['L','C','R']},sequence={'type':'array','minItems':8,'maxItems':8,'items':{'type':'integer','minimum':-24,'maximum':24}},operators={'type':'array','minItems':4,'maxItems':4,'items':{'type':'object','properties':{k:{'type':'integer','minimum':v[0],'maximum':v[1]} for k,v in engine.OP_RANGES.items()},'additionalProperties':False}})
PATCH_SCHEMA['additionalProperties']=False
TOOLS=[
 {'name':'list_presets','description':'List factory SFX presets, chips and editing capabilities. No files are written.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
 {'name':'get_preset','description':'Get a complete patch by preset index (0-based). Use list_presets to find a chip-specific template, then modify its parameters.','inputSchema':{'type':'object','properties':{'index':{'type':'integer','minimum':0,'maximum':len(engine.presets())-1}},'required':['index'],'additionalProperties':False}},
 {'name':'validate_patch','description':'Validate and complete a patch, returning exact settings and event count.','inputSchema':{'type':'object','properties':{'patch':PATCH_SCHEMA},'required':['patch'],'additionalProperties':False}},
 {'name':'render_sound','description':'Render a patch through the ymfm chip emulator. Write WAV and editable patch JSON in a new local outputs folder; return absolute paths.','inputSchema':{'type':'object','properties':{'patch':PATCH_SCHEMA},'required':['patch'],'additionalProperties':False}},
 {'name':'export_sound','description':'Create AI handoff package: WAV, VGM, editable patch, register timeline, C header, Markdown integration guide and SHA-256 manifest. Writes only under the local outputs folder.','inputSchema':{'type':'object','properties':{'patch':PATCH_SCHEMA},'required':['patch'],'additionalProperties':False}},
 {'name':'get_handoff_text','description':'Return complete AI integration text and register timeline for a patch; does not write files.','inputSchema':{'type':'object','properties':{'patch':PATCH_SCHEMA},'required':['patch'],'additionalProperties':False}},
]
for tool in TOOLS: tool['annotations']={'readOnlyHint':tool['name'] not in ('render_sound','export_sound'),'destructiveHint':False,'idempotentHint':tool['name'] not in ('render_sound','export_sound'),'openWorldHint':False}

def result(data): return {'content':[{'type':'text','text':data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)}],'isError':False}
def call(name,args):
    if name not in [t['name'] for t in TOOLS]: raise ValueError('Unknown tool')
    if not isinstance(args,dict): raise ValueError('Arguments must be an object')
    if name=='list_presets':
        return result(dict(presets=[dict(index=i,name=p['name'],chip=p['chip']) for i,p in enumerate(engine.presets())],chips=engine.CHIPS,notes='Single channel; OPNA ADPCM/rhythm unsupported; PSG uses YM2149; hardware not verified.'))
    if name=='get_preset':
        i=engine.number(args.get('index'),0,len(engine.presets())-1,True); return result(engine.presets()[i])
    p=engine.validate(args.get('patch'))
    if name=='validate_patch':
        _,events,frames=engine.compile_patch(p);return result(dict(patch=p,eventCount=len(events),totalSamples=frames,timebase=44100))
    if name=='get_handoff_text':return result(handoff.description(p))
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]
    directory=OUTPUT/stamp;directory.mkdir(parents=True,exist_ok=False)
    if name=='render_sound': files={'sound.wav':engine.render(p),'patch.json':json.dumps(p,ensure_ascii=False,indent=2).encode('utf-8')}
    else: files=handoff.files(p)
    for filename,content in files.items(): (directory/filename).write_bytes(content)
    if name=='export_sound':
        import zipfile
        with zipfile.ZipFile(directory/'ai-package.zip','w',zipfile.ZIP_DEFLATED) as z:
            for filename,content in files.items():z.writestr(filename,content)
    return result(dict(directory=str(directory.resolve()),files={f.name:str(f.resolve()) for f in directory.iterdir()},chip=p['chip'],name=p['name']))

def dispatch(message):
    if not isinstance(message,dict) or message.get('jsonrpc')!='2.0' or not isinstance(message.get('method'),str):
        return {'jsonrpc':'2.0','id':message.get('id') if isinstance(message,dict) else None,'error':{'code':-32600,'message':'Invalid Request'}}
    if 'id' not in message:return None
    ident=message['id'];method=message['method'];params=message.get('params',{})
    def ok(value):return {'jsonrpc':'2.0','id':ident,'result':value}
    if method=='initialize':
        version=params.get('protocolVersion')
        return ok({'protocolVersion':version if version in SUPPORTED else SUPPORTED[0],'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'retro-sfx-studio','version':'1.1.0'},'instructions':'Create retro chip sound effects. Start with list_presets/get_preset; use export_sound to hand off assets to a game project. Files are local. Preserve BGM and shared chip registers when integrating.'})
    if method=='ping':return ok({})
    if method=='tools/list':return ok({'tools':TOOLS})
    if method=='tools/call':
        try:return ok(call(params.get('name'),params.get('arguments',{})))
        except Exception as e:return ok({'content':[{'type':'text','text':str(e)}],'isError':True})
    return {'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Method not found'}}

def main():
    # No web server needed. MCP uses UTF-8, one JSON-RPC message per line.
    for raw in sys.stdin.buffer:
        try:
            if len(raw)>262144: raise ValueError('Request too large')
            message=json.loads(raw);reply=dispatch(message)
        except Exception:
            reply={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Parse error'}}
        if reply is not None:
            sys.stdout.buffer.write(json.dumps(reply,ensure_ascii=False,separators=(',',':')).encode('utf-8')+b'\n');sys.stdout.buffer.flush()

if __name__=='__main__': main()
