from __future__ import annotations


class ContentSecurityPolicyLogic:
    """Create a strict nonce-based CSP with explicit integration boundaries."""

    def build(self, nonce: str, *, is_production: bool) -> str:
        directives = [
            "default-src 'self'",
            "base-uri 'none'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self' https://accounts.google.com https://github.com",
            (
                "script-src "
                f"'nonce-{nonce}' 'strict-dynamic' 'self' https: http:"
            ),
            (
                "style-src 'self' 'unsafe-inline' "
                "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net "
                "https://fonts.googleapis.com"
            ),
            (
                "font-src 'self' data: "
                "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net "
                "https://fonts.gstatic.com"
            ),
            "img-src 'self' data: blob: https:",
            (
                "connect-src 'self' "
                "https://www.google.com https://www.gstatic.com"
            ),
            (
                "frame-src 'self' "
                "https://www.google.com https://recaptcha.google.com"
            ),
            "worker-src 'self' blob:",
            "manifest-src 'self'",
        ]
        if is_production:
            directives.append("upgrade-insecure-requests")
        return "; ".join(directives)
