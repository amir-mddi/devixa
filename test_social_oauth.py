import os
import time
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs

import requests

BACKEND_BASE_URL = "http://localhost:8000"
REDIRECT_URI = "http://localhost:3000/oauth/callback"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID",
                             "118576697846-gi6mnabv74beosa9npe2t0e5mq9nfm67.apps.googleusercontent.com")
GITHUB_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    oauth_code = None
    oauth_error = None

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        OAuthCallbackHandler.oauth_code = query.get("code", [None])[0]
        OAuthCallbackHandler.oauth_error = query.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if OAuthCallbackHandler.oauth_code:
            self.wfile.write(
                b"""
                <html>
                    <body>
                        <h2>OAuth code received successfully.</h2>
                        <p>You can close this browser tab and return to terminal.</p>
                    </body>
                </html>
                """
            )
        else:
            self.wfile.write(
                b"""
                <html>
                    <body>
                        <h2>OAuth failed.</h2>
                        <p>No code received. Check terminal.</p>
                    </body>
                </html>
                """
            )

    def log_message(self, format, *args):
        return


def wait_for_oauth_code(timeout_seconds=180):
    server = HTTPServer(("localhost", 3000), OAuthCallbackHandler)

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    print("Waiting for OAuth callback on http://localhost:3000/oauth/callback ...")

    started_at = time.time()

    while time.time() - started_at < timeout_seconds:
        if OAuthCallbackHandler.oauth_code or OAuthCallbackHandler.oauth_error:
            server.shutdown()
            return OAuthCallbackHandler.oauth_code, OAuthCallbackHandler.oauth_error

        time.sleep(0.5)

    server.shutdown()
    raise TimeoutError("OAuth callback timeout. No code received.")


def build_google_auth_url():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def build_github_auth_url():
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "read:user user:email",
    }

    return "https://github.com/login/oauth/authorize?" + urlencode(params)


def send_code_to_backend(provider, code):
    url = f"{BACKEND_BASE_URL}/api/v1/account/oauth/{provider}/"

    response = requests.post(
        url,
        json={
            "code": code,
            "redirectUri": REDIRECT_URI,
        },
        timeout=20,
    )

    print("\nBackend status:", response.status_code)

    try:
        print("Backend response:")
        print(response.json())
    except Exception:
        print(response.text)


def main():
    provider = input("Provider? google/github: ").strip().lower()

    if provider not in {"google", "github"}:
        raise ValueError("Provider must be google or github")

    if provider == "google":
        auth_url = build_google_auth_url()
    else:
        auth_url = build_github_auth_url()

    print("\nOpening browser:")
    print(auth_url)

    webbrowser.open(auth_url)

    code, error = wait_for_oauth_code()

    if error:
        raise RuntimeError(f"OAuth provider returned error: {error}")

    if not code:
        raise RuntimeError("No OAuth code received.")

    print("\nOAuth code received.")
    print("Sending code to Django backend...")

    send_code_to_backend(provider, code)


if __name__ == "__main__":
    main()
