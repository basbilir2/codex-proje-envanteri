"""Loopback-only desktop web UI. No cloud service or credentials are required."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import secrets
import shutil
import threading
from urllib.parse import urlparse, parse_qs, unquote
import webbrowser

from .pipeline import Studio, write_json


class Server(ThreadingHTTPServer):
    daemon_threads = True


def handler(studio, token):
    static = Path(__file__).with_name("web")
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def authorized(self):
            query = parse_qs(urlparse(self.path).query)
            supplied = self.headers.get("X-Studio-Token", query.get("t",[""])[0])
            expected_host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != expected_host or not hmac.compare_digest(supplied,token):
                self.json_response({"error":"Yerel uygulama erişimi gerekli. Başlatıcıdan yeniden açın."},403)
                return False
            origin = self.headers.get("Origin")
            if origin and origin != "http://"+expected_host:
                self.send_error(403,"Origin rejected")
                return False
            return True

        def send_content_headers(self, status, mime, length):
            self.send_response(status)
            self.send_header("Content-Type",mime)
            self.send_header("Content-Length",str(length))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
            self.send_header("Content-Security-Policy","default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")

        def json_response(self, value, status=200):
            body = json.dumps(value,ensure_ascii=False,allow_nan=False).encode("utf-8")
            self.send_content_headers(status,"application/json; charset=utf-8",len(body))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                if self.authorized():
                    self.json_response(studio.snapshot())
                return
            if parsed.path.startswith("/files/"):
                if not self.authorized():
                    return
                pieces = parsed.path.split("/",3)
                roots = {"local":studio.local,"outputs":studio.root/"outputs"}
                if len(pieces)!=4 or pieces[2] not in roots:
                    self.send_error(404)
                    return
                root = roots[pieces[2]].resolve()
                path = (root/unquote(pieces[3])).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    self.send_error(404)
                    return
            else:
                names = {"/":"index.html","/app.js":"app.js","/style.css":"style.css"}
                if parsed.path not in names:
                    self.send_error(404)
                    return
                path = static/names[parsed.path]
            mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_content_headers(200,mime,path.stat().st_size)
            if path.suffix.lower() in (".tif",".tiff",".blend"):
                self.send_header("Content-Disposition",f'attachment; filename="{path.name}"')
            self.end_headers()
            try:
                with path.open("rb") as stream:
                    shutil.copyfileobj(stream,self.wfile,1024*1024)
            except (BrokenPipeError,ConnectionResetError):
                pass

        def do_POST(self):
            if not self.authorized():
                return
            try:
                length = int(self.headers.get("Content-Length","0"))
                if not 0 < length <= 512*1024*1024:
                    raise ValueError("Dosya veya istek boyutu 512 MB sınırını aşıyor.")
                data = self.rfile.read(length)
                parsed = urlparse(self.path)
                if parsed.path == "/api/upload":
                    query = parse_qs(parsed.query)
                    kind = query.get("kind",["photo"])[0]
                    name = unquote(self.headers.get("X-Filename","file.png"))
                    if kind == "photo":
                        result = studio.add_photo(data,name)
                    elif kind == "depth":
                        studio.add_depth(query["asset"][0],data,name,query.get("convention",["white-near"])[0])
                        result = {"ok":True}
                    else:
                        result = studio.upload_resource(data,name,kind)
                else:
                    request = json.loads(data)
                    if parsed.path == "/api/jobs":
                        result = {"id":studio.start(request)}
                    elif parsed.path == "/api/cancel":
                        studio.cancel(request["id"])
                        result = {"ok":True}
                    elif parsed.path == "/api/profile":
                        result = studio.profile(request["name"],request)
                    elif parsed.path == "/api/shutdown":
                        studio.close()
                        threading.Thread(target=self.server.shutdown,daemon=True).start()
                        result = {"ok":True}
                    else:
                        self.send_error(404)
                        return
                self.json_response(result)
            except Exception as error:
                self.json_response({"error":str(error)},400)
    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lenticular Studio yerel uygulama")
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--no-browser",action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    # Reuse a live instance rather than allowing concurrent writers to the same project.
    info_path = root/".studio/server.json"
    if info_path.is_file():
        try:
            import urllib.request
            info = json.loads(info_path.read_text(encoding="utf-8"))
            address = urlparse(info["url"])
            if address.hostname == "127.0.0.1" and Path(info["root"]).resolve() == root:
                response = json.load(urllib.request.urlopen(info["url"].replace('/?','/api/state?'),timeout=1))
                if response.get("schema_version") == 1:
                    if not args.no_browser:
                        webbrowser.open(info["url"])
                    return
        except (OSError,ValueError,KeyError):
            pass
    studio = Studio(root)
    # Keep the existing local capability across restarts so open pages can upload.
    token = None
    if info_path.is_file():
        try:
            previous = json.loads(info_path.read_text(encoding="utf-8"))
            candidate = parse_qs(urlparse(previous["url"]).query).get("t",[""])[0]
            if Path(previous["root"]).resolve()==root and len(candidate)>=32 and all(c.isalnum() or c in "_-" for c in candidate):
                token = candidate
        except (OSError,ValueError,KeyError):
            pass
    token = token or secrets.token_urlsafe(32)
    try:
        server = Server(("127.0.0.1",args.port),handler(studio,token))
    except OSError:
        server = Server(("127.0.0.1",0),handler(studio,token))
    url = f"http://127.0.0.1:{server.server_port}/?t={token}"
    import os
    write_json(studio.local/"server.json",dict(url=url,port=server.server_port,pid=os.getpid(),root=str(root)))
    print("Lenticular Studio hazır.",flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        studio.close()
        server.server_close()


if __name__ == "__main__":
    main()
