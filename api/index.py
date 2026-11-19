import os
import sys
import urllib.parse

# Ensure root folder is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app


class VercelPathMiddleware:
    """Restores the original incoming request path from Vercel rewrite parameter."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        if "path=" in qs:
            params = urllib.parse.parse_qs(qs, keep_blank_values=True)
            path_values = params.pop("path", None)
            if path_values and path_values[0]:
                orig_path = path_values[0]
                environ["PATH_INFO"] = "/" + orig_path.lstrip("/")
            else:
                environ["PATH_INFO"] = "/"
            environ["QUERY_STRING"] = urllib.parse.urlencode(params, doseq=True)

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()
