"""Package only deliverable files; omit generated test outputs and development caches."""
from pathlib import Path
import hashlib
import json
import zipfile
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'releases';out.mkdir(exist_ok=True)
def write_zip(path,items):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for source,name in items:z.write(source,name)
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    return dict(file=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
binary=ROOT/'dist/RetroSFX'
items=[(f,'RetroSFX/'+f.relative_to(binary).as_posix()) for f in sorted(binary.rglob('*')) if f.is_file() and 'outputs' not in f.relative_to(binary).parts]
results=[write_zip(out/'RetroSFX-Studio-v1.0.0-win-x64.zip',items)]
files=[]
for filename in ['LICENSE','DISCLAIMER.md','requirements-dev.txt','README.md','MCP_SETUP.md','THIRD_PARTY.md','engine.py','server.py','handoff.py','mcp_server.py','launcher.py','start.bat','build.ps1','CMakeLists.txt','.gitignore','.gitattributes']:
    files.append(ROOT/filename)
for folder in ['static','native','tests','tools','licenses']:
    files.extend(f for f in (ROOT/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts)
files.extend(f for f in (ROOT/'vendor/ymfm/src').rglob('*') if f.is_file())
files.extend([ROOT/'vendor/ymfm/LICENSE',ROOT/'vendor/ymfm/README.md',ROOT/'vendor/ymfm/GeneralInfo.md'])
files.append(ROOT/'bin/retro_render.exe')
results.append(write_zip(out/'RetroSFX-Studio-v1.0.0-source.zip',[(f,'retro-sfx-studio/'+f.relative_to(ROOT).as_posix()) for f in sorted(files)]))
(out/'SHA256.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
