import json
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query = {
            key: values[0] if values else ""
            for key, values in parse_qs(parsed_url.query).items()
        }
        self.server.oauth_query = query

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if query.get("code"):
            body = """
            <html>
                <body>
                    <h2>OAuth code received successfully.</h2>
                    <p>You can close this browser tab and return to terminal.</p>
                </body>
            </html>
            """
        else:
            body = """
            <html>
                <body>
                    <h2>OAuth failed.</h2>
                    <p>No code was received. Check the terminal output.</p>
                </body>
            </html>
            """

        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        return


class LocalOAuthServer(HTTPServer):
    oauth_query = None


class Command(BaseCommand):
    help = "Run a local browser-based Google/GitHub OAuth test and call the Django OAuth API."

    def add_arguments(self, parser):
        parser.add_argument("provider", choices=["google", "github"], help="OAuth provider to test.")
        parser.add_argument(
            "--backend-url",
            default="http://localhost:8000",
            help="Running Django backend base URL. Default: http://localhost:8000",
        )
        parser.add_argument(
            "--redirect-uri",
            default=None,
            help="Redirect URI registered in Google/GitHub. Default: first OAUTH_ALLOWED_REDIRECT_URIS value.",
        )
        parser.add_argument("--client-id", default=None, help="Override OAuth client ID.")
        parser.add_argument("--timeout", type=int, default=180, help="Seconds to wait for browser callback.")
        parser.add_argument("--no-browser", action="store_true", help="Print the URL without opening the browser.")

    def handle(self, *args, **options):
        provider = options["provider"]
        backend_url = options["backend_url"].rstrip("/")
        redirect_uri = options["redirect_uri"] or self._default_redirect_uri()
        client_id = options["client_id"] or self._client_id(provider)
        timeout = options["timeout"]
        state = secrets.token_urlsafe(32)

        self._validate_redirect_uri_for_local_server(redirect_uri)

        auth_url = self._build_auth_url(
            provider=provider,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
        )

        parsed_redirect = urlparse(redirect_uri)
        port = parsed_redirect.port or (443 if parsed_redirect.scheme == "https" else 80)
        server = LocalOAuthServer((parsed_redirect.hostname, port), OAuthCallbackHandler)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        self.stdout.write(self.style.WARNING("Opening OAuth authorization URL:"))
        self.stdout.write(auth_url)

        if not options["no_browser"]:
            webbrowser.open(auth_url)

        query = self._wait_for_callback(server=server, timeout=timeout)
        server.server_close()

        self.stdout.write("\nProvider redirected this query:")
        self.stdout.write(json.dumps(query, indent=2, ensure_ascii=False))

        if query.get("error"):
            raise CommandError(f"OAuth provider error: {query['error']}")

        received_state = query.get("state") or ""
        if not secrets.compare_digest(received_state, state):
            raise CommandError("Invalid OAuth state received. Do not send this code to backend.")

        code = query.get("code")
        if not code:
            raise CommandError("OAuth provider did not return a code.")

        endpoint = f"{backend_url}/api/v1/account/oauth/{provider}/"
        response_status, response_body = self._post_json(
            endpoint,
            {
                "code": code,
                "redirectUri": redirect_uri,
            },
        )

        self.stdout.write("\nBackend response:")
        self.stdout.write(f"HTTP {response_status}")
        self.stdout.write(json.dumps(response_body, indent=2, ensure_ascii=False))

        if 200 <= response_status < 300:
            self.stdout.write(self.style.SUCCESS("\nOAuth test finished successfully."))
        else:
            raise CommandError("OAuth test failed. Check the backend response above.")

    @staticmethod
    def _default_redirect_uri() -> str:
        allowed_redirects = getattr(settings, "OAUTH_ALLOWED_REDIRECT_URIS", [])
        if allowed_redirects:
            return allowed_redirects[0]
        return "http://localhost:3000/oauth/callback"

    @staticmethod
    def _client_id(provider: str) -> str:
        setting_name = f"{provider.upper()}_OAUTH_CLIENT_ID"
        client_id = getattr(settings, setting_name, "")
        if not client_id:
            raise CommandError(f"Missing {setting_name}. Add it to your env file or pass --client-id.")
        return client_id

    @staticmethod
    def _validate_redirect_uri_for_local_server(redirect_uri: str) -> None:
        parsed = urlparse(redirect_uri)
        if parsed.scheme != "http":
            raise CommandError("This local test command only serves plain http:// redirect URIs.")
        if parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise CommandError("Use localhost or 127.0.0.1 for local OAuth testing.")

    @staticmethod
    def _build_auth_url(*, provider: str, client_id: str, redirect_uri: str, state: str) -> str:
        if provider == "google":
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
            return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return "https://github.com/login/oauth/authorize?" + urlencode(params)

    @staticmethod
    def _wait_for_callback(*, server: LocalOAuthServer, timeout: int) -> dict:
        started_at = time.time()
        while time.time() - started_at < timeout:
            if server.oauth_query is not None:
                server.shutdown()
                return server.oauth_query
            time.sleep(0.25)

        server.shutdown()
        raise CommandError("Timed out waiting for OAuth callback.")

    @staticmethod
    def _post_json(url: str, payload: dict) -> tuple[int, dict]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                status = response.status
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            status = exc.code
        except URLError as exc:
            raise CommandError(f"Could not call backend: {exc}") from exc

        try:
            return status, json.loads(body) if body else {}
        except json.JSONDecodeError:
            return status, {"raw": body}
