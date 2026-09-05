from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class SpaHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        parsed = urlparse(self.path)
        requested = parsed.path

        translated = Path(self.translate_path(requested))

        if (
            requested != "/"
            and not translated.exists()
            and "." not in Path(requested).name
        ):
            self.path = "/index.html"

        return super().send_head()

    def end_headers(self):
        if self.path.endswith("index.html") or self.path == "/":
            self.send_header(
                "Cache-Control",
                "no-cache, no-store, must-revalidate",
            )

        self.send_header(
            "X-Content-Type-Options",
            "nosniff",
        )
        self.send_header(
            "X-Frame-Options",
            "SAMEORIGIN",
        )

        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the built React SPA with route fallback."
    )
    parser.add_argument("--directory", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    index_file = directory / "index.html"

    if not index_file.exists():
        raise SystemExit(
            f"Frontend build not found: {index_file}"
        )

    handler = partial(
        SpaHandler,
        directory=str(directory),
    )

    server = ThreadingHTTPServer(
        (args.host, args.port),
        handler,
    )

    print(
        f"Serving frontend at http://{args.host}:{args.port}",
        flush=True,
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
