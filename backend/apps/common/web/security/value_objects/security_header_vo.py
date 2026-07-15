from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContentSecurityPolicyConfig:
    enabled: bool
    report_only: bool = False


class SecurityHeaderVO:
    CSP_HEADER = "Content-Security-Policy"
    CSP_REPORT_ONLY_HEADER = "Content-Security-Policy-Report-Only"

    PERMISSIONS_POLICY_HEADER = "Permissions-Policy"
    PERMISSIONS_POLICY_VALUE = (
        "accelerometer=(), ambient-light-sensor=(), autoplay=(), battery=(), "
        "camera=(), display-capture=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    )

    CROSS_ORIGIN_OPENER_POLICY_HEADER = "Cross-Origin-Opener-Policy"
    CROSS_ORIGIN_OPENER_POLICY_VALUE = "same-origin-allow-popups"

    ORIGIN_AGENT_CLUSTER_HEADER = "Origin-Agent-Cluster"
    ORIGIN_AGENT_CLUSTER_VALUE = "?1"

    PERMITTED_CROSS_DOMAIN_POLICIES_HEADER = "X-Permitted-Cross-Domain-Policies"
    PERMITTED_CROSS_DOMAIN_POLICIES_VALUE = "none"

    DEFAULT_HEADERS = (
        (PERMISSIONS_POLICY_HEADER, PERMISSIONS_POLICY_VALUE),
        (CROSS_ORIGIN_OPENER_POLICY_HEADER, CROSS_ORIGIN_OPENER_POLICY_VALUE),
        (ORIGIN_AGENT_CLUSTER_HEADER, ORIGIN_AGENT_CLUSTER_VALUE),
        (
            PERMITTED_CROSS_DOMAIN_POLICIES_HEADER,
            PERMITTED_CROSS_DOMAIN_POLICIES_VALUE,
        ),
    )
