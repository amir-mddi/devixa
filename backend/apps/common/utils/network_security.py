from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit


class UnsafeOutboundUrlError(ValueError):
    pass


def force_https_scheme(value: str | None) -> str:
    """Return an HTTP(S) URL with HTTPS as the public-facing scheme.

    Relative URLs and non-HTTP schemes are intentionally left untouched. This
    makes the helper safe for presentation and DTO normalization without
    breaking local media paths, ``mailto:``, or Telegram deep links.
    """

    raw_value = str(value or "").strip()
    if not raw_value:
        return ""
    if raw_value.startswith("//"):
        return f"https:{raw_value}"

    parsed = urlsplit(raw_value)
    if parsed.scheme.lower() != "http":
        return raw_value

    return urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, parsed.fragment))


def _is_allowed_host(hostname: str, allowed_hosts: Iterable[str]) -> bool:
    normalized = hostname.rstrip(".").lower()
    for raw_host in allowed_hosts:
        allowed = str(raw_host or "").strip().rstrip(".").lower()
        if not allowed:
            continue
        if normalized == allowed or normalized.endswith(f".{allowed}"):
            return True
    return False


def _assert_public_address(address: str) -> None:
    parsed = ipaddress.ip_address(address)
    if not parsed.is_global:
        raise UnsafeOutboundUrlError("Private or non-routable network addresses are not allowed.")


def validate_public_https_url(
    value: str,
    *,
    allowed_hosts: Iterable[str] = (),
    resolve_dns: bool = False,
    max_length: int = 2048,
) -> str:
    """Validate an outbound HTTPS URL before the server fetches it.

    The optional host allowlist is strongly recommended for provider-generated
    file URLs. DNS resolution is performed only at the final outbound boundary,
    not in serializers, so normal form validation does not depend on DNS.
    """

    value = str(value or "").strip()
    if not value:
        raise UnsafeOutboundUrlError("URL is required.")
    if len(value) > max_length:
        raise UnsafeOutboundUrlError("URL is too long.")

    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise UnsafeOutboundUrlError("Only HTTPS URLs are allowed.")
    if parsed.username or parsed.password:
        raise UnsafeOutboundUrlError("URL credentials are not allowed.")
    if parsed.fragment:
        raise UnsafeOutboundUrlError("URL fragments are not allowed.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
        raise UnsafeOutboundUrlError("Local network URLs are not allowed.")

    configured_hosts = tuple(allowed_hosts)
    if configured_hosts and not _is_allowed_host(hostname, configured_hosts):
        raise UnsafeOutboundUrlError("URL host is not in the configured allowlist.")

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        _assert_public_address(hostname)

    if resolve_dns:
        try:
            answers = socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UnsafeOutboundUrlError("URL hostname could not be resolved.") from exc
        if not answers:
            raise UnsafeOutboundUrlError("URL hostname could not be resolved.")
        for answer in answers:
            _assert_public_address(answer[4][0])

    return value


def normalize_public_https_url(
    value: str | None,
    *,
    allowed_hosts: Iterable[str] = (),
    resolve_dns: bool = False,
    max_length: int = 2048,
) -> str:
    """Upgrade an HTTP URL to HTTPS and validate it as a public URL."""

    normalized = force_https_scheme(value)
    if not normalized:
        return ""

    # Public navigation links may legitimately use fragments (for example, a
    # documentation section). The stricter outbound-fetch validator rejects
    # fragments, so validate the network target without the fragment and then
    # preserve the original fragment for browser navigation.
    parsed = urlsplit(normalized)
    validation_target = urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.query, "")
    )
    validate_public_https_url(
        validation_target,
        allowed_hosts=allowed_hosts,
        resolve_dns=resolve_dns,
        max_length=max_length,
    )
    return normalized
