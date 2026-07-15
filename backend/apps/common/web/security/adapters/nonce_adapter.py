from __future__ import annotations

import secrets


class SecurityNonceAdapter:
    """Generate a cryptographically strong per-response CSP nonce."""

    @staticmethod
    def generate() -> str:
        return secrets.token_urlsafe(24)
