import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import engine
import handoff

STATIC=engine.ROOT/'static'
class Handler(BaseHTTPRequestHandler):
    def reply(self,data,kind='application/json; charset=utf-8',status=200):
        if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers(); self.wfile.write(data)
    def allowed(self):
        host=self.headers.get('Host','')
        if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'): return False
        origin=self.headers.get('Origin')
        return not origin or origin in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}')
    def do_GET(self):
        if not self.allowed(): return self.reply({'error':'Local access only'},status=403)
        route=urlparse(self.path).path
        if route=='/api/info': return self.reply(dict(default=engine.DEFAULT,presets=engine.presets(),chips=engine.CHIPS,engine='ymfm 81aec25'))
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if route not in files: return self.reply({'error':'Not found'},status=404)
        name,kind=files[route]; self.reply((STATIC/name).read_bytes(),kind)
    def do_POST(self):
        if not self.allowed(): return self.reply({'error':'Local access only'},status=403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=65536: raise ValueError('パッチのサイズが不正です。')
            p=engine.validate(json.loads(self.rfile.read(size)))
            route=urlparse(self.path).path
            if route=='/api/render': self.reply(engine.render(p),'audio/wav')
            elif route=='/api/vgm': self.reply(engine.vgm(p),'application/octet-stream')
            elif route=='/api/registers': self.reply(engine.register_json(p))
            elif route=='/api/header': self.reply(engine.c_header(p),'text/plain; charset=utf-8')
            elif route=='/api/validate': self.reply(p)
            elif route=='/api/handoff': self.reply(handoff.description(p).encode('utf-8'),'text/markdown; charset=utf-8')
            elif route=='/api/bundle': self.reply(handoff.bundle(p),'application/zip')
            else: self.reply({'error':'Not found'},status=404)
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc: self.reply({'error':str(exc)},status=400)
        except Exception as exc:
            print(f'Render error: {exc}',flush=True); self.reply({'error':'音声の生成に失敗しました。サーバーのログを確認してください。'},status=500)
    def log_message(self,fmt,*args): print(fmt%args,flush=True)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=7911); parser.add_argument('--no-browser',action='store_true'); args=parser.parse_args()
    url=f'http://127.0.0.1:{args.port}'
    try:
        server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError:
        # Reopen an already running instance, without replacing another service.
        from urllib.request import urlopen
        try:
            with urlopen(url+'/api/info',timeout=2) as response: running=json.load(response)
            if running.get('engine')!='ymfm 81aec25': raise RuntimeError('Port is in use')
        except Exception: raise RuntimeError(f'Port {args.port} is in use. Specify another --port.')
        if not args.no_browser:webbrowser.open(url)
        print(f'Already running: {url}',flush=True)
        return
    print(f'Retro SFX Studio: {url}',flush=True)
    if not args.no_browser: threading.Timer(.6,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
