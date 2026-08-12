from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DIST_DIR = Path(__file__).resolve().parent / "dist"


class SPARequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def send_head(self):
        requested_path = DIST_DIR / self.path.lstrip("/").split("?", 1)[0]
        if self.path != "/" and not requested_path.exists():
            self.path = "/index.html"
        return super().send_head()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 5173), SPARequestHandler)
    print("Frontend running at http://127.0.0.1:5173", flush=True)
    server.serve_forever()
