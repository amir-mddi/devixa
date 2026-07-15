from rest_framework.throttling import UserRateThrottle


class BaseAuthenticatedThrottle(UserRateThrottle):
    rate = None
    scope = None

    def allow_request(self, request, view):
        if request.user.is_authenticated:
            return super().allow_request(request, view)
        return True


class LoginUserThrottling(BaseAuthenticatedThrottle):
    rate = '20/second'
    scope = 'login'


class AnonymousUserThrottling(UserRateThrottle):
    rate = '1000/hour'
    scope = 'anon'

    def allow_request(self, request, view):
        if not request.user.is_authenticated:
            return super().allow_request(request, view)
        return True


class IrTransactionsThrottle(BaseAuthenticatedThrottle):
    rate = '10/minute'
    scope = 'ir_transactions'


class CryptoDepositThrottle(BaseAuthenticatedThrottle):
    rate = '10/minute'
    scope = 'crypto_deposit'


class CryptoWithdrawThrottle(BaseAuthenticatedThrottle):
    rate = '30/minute'
    scope = 'crypto_withdraw'


class TradeThrottle(BaseAuthenticatedThrottle):
    rate = '400/minute'
    scope = 'trade'


class OrderbookThrottle(BaseAuthenticatedThrottle):
    rate = '100/minute'
    scope = 'orderbook'


class BalancesThrottle(BaseAuthenticatedThrottle):
    rate = '100/minute'
    scope = 'balances'


class AddressThrottle(BaseAuthenticatedThrottle):
    rate = '10/minute'
    scope = 'address'


class CurrencyThrottle(BaseAuthenticatedThrottle):
    rate = '10/minute'
    scope = 'currency'

class LoginThrottle(BaseAuthenticatedThrottle):
    rate = '10/minute'
    scope = 'login'


# core/throttling.py


import hashlib
import time
from dataclasses import dataclass
from typing import Iterable

from django.core.cache import cache

from backend.apps.common.utils.common_utils import CommonUtils
from django.utils.encoding import force_str
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle


@dataclass(frozen=True)
class Rate:
    limit: int
    duration: int


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class RateParser:
    PERIODS = {
        "s": 1,
        "sec": 1,
        "second": 1,
        "seconds": 1,
        "m": 60,
        "min": 60,
        "minute": 60,
        "minutes": 60,
        "h": 60 * 60,
        "hour": 60 * 60,
        "hours": 60 * 60,
        "d": 60 * 60 * 24,
        "day": 60 * 60 * 24,
        "days": 60 * 60 * 24,
    }

    @classmethod
    def parse(cls, value: str) -> Rate:
        try:
            raw_limit, raw_period = value.split("/", 1)
            limit = int(raw_limit)
            duration = cls.PERIODS[raw_period.lower()]
        except (ValueError, KeyError):
            raise ValueError(f"Invalid rate format: {value!r}")

        if limit <= 0:
            raise ValueError("Rate limit must be positive.")

        return Rate(limit=limit, duration=duration)


class ClientIP:

    @staticmethod
    def get(request: Request) -> str:
        return CommonUtils.get_client_ip(request)


class FixedWindowLimiter:

    KEY_VERSION = "v1"
    KEY_PREFIX = "throttle"

    def __init__(self, scope: str, rate: str):
        self.scope = scope
        self.rate = RateParser.parse(rate)

    def allow(self, identity: str) -> None:
        key = self.build_key(identity)
        current = self.incr_with_ttl(key, self.rate.duration)

        if current > self.rate.limit:
            raise RateLimitExceeded(retry_after=self.rate.duration)

    def build_key(self, identity: str) -> str:
        window = int(time.time()) // self.rate.duration
        safe_identity = self.hash_identity(identity)

        return (
            f"{self.KEY_PREFIX}:"
            f"{self.KEY_VERSION}:"
            f"{self.scope}:"
            f"{safe_identity}:"
            f"{window}"
        )

    @staticmethod
    def hash_identity(identity: str) -> str:

        normalized = force_str(identity).strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def incr_with_ttl(key: str, ttl: int) -> int:
        try:
            return cache.incr(key)
        except ValueError:
            created = cache.add(key, 1, timeout=ttl)

            if created:
                return 1

            return cache.incr(key)


class BaseFixedWindowThrottle(BaseThrottle):
    scope: str | None = None
    rate: str | None = None

    def __init__(self):
        if not self.scope:
            raise ValueError(f"{self.__class__.__name__}.scope is required")

        if not self.rate:
            raise ValueError(f"{self.__class__.__name__}.rate is required")

        self.limiter = FixedWindowLimiter(scope=self.scope, rate=self.rate)
        self.retry_after: int | None = None

    def get_identity(self, request: Request, view) -> str | None:
        raise NotImplementedError

    def allow_request(self, request: Request, view) -> bool:
        identity = self.get_identity(request, view)

        if identity is None:
            return True

        try:
            self.limiter.allow(identity)
            return True
        except RateLimitExceeded as exc:
            self.retry_after = exc.retry_after
            return False

    def wait(self) -> int | None:
        return self.retry_after


class AuthenticatedUserThrottle(BaseFixedWindowThrottle):
    scope = "authenticated_user"
    rate = "1000/hour"

    def get_identity(self, request: Request, view) -> str | None:
        user = request.user

        if not user or not user.is_authenticated:
            return None

        return f"user:{user.pk}"


class AnonymousIPThrottle(BaseFixedWindowThrottle):
    scope = "anonymous_ip"
    rate = "300/hour"

    def get_identity(self, request: Request, view) -> str | None:
        user = request.user

        if user and user.is_authenticated:
            return None

        ip = ClientIP.get(request)

        if not ip:
            return None

        return f"ip:{ip}"


@dataclass(frozen=True)
class ThrottleRule:
    scope: str
    rate: str
    identity: str


class MultiRuleThrottle(BaseThrottle):

    def __init__(self):
        self.retry_after: int | None = None

    def get_rules(self, request: Request, view) -> Iterable[ThrottleRule]:
        raise NotImplementedError

    def allow_request(self, request: Request, view) -> bool:
        for rule in self.get_rules(request, view):
            limiter = FixedWindowLimiter(scope=rule.scope, rate=rule.rate)

            try:
                limiter.allow(rule.identity)
            except RateLimitExceeded as exc:
                self.retry_after = exc.retry_after
                return False

        return True

    def wait(self) -> int | None:
        return self.retry_after


class LoginThrottle(MultiRuleThrottle):
    IP_RATE = "30/minute"
    IDENTIFIER_RATE = "10/minute"
    IP_IDENTIFIER_RATE = "5/minute"

    def get_rules(self, request: Request, view) -> Iterable[ThrottleRule]:
        ip = ClientIP.get(request)
        identifier = self.get_identifier(request)

        rules: list[ThrottleRule] = []

        if ip:
            rules.append(
                ThrottleRule(
                    scope="login_ip",
                    rate=self.IP_RATE,
                    identity=f"ip:{ip}",
                )
            )

        if identifier:
            rules.append(
                ThrottleRule(
                    scope="login_identifier",
                    rate=self.IDENTIFIER_RATE,
                    identity=f"identifier:{identifier}",
                )
            )

        if ip and identifier:
            rules.append(
                ThrottleRule(
                    scope="login_ip_identifier",
                    rate=self.IP_IDENTIFIER_RATE,
                    identity=f"ip:{ip}:identifier:{identifier}",
                )
            )

        return rules

    @staticmethod
    def get_identifier(request: Request) -> str | None:
        value = (
            request.data.get("email")
            or request.data.get("username")
            or request.data.get("phone")
        )

        if not value:
            return None

        return str(value).strip().lower()

class PaymentCallbackThrottle(BaseFixedWindowThrottle):
    scope = "payment_callback"
    rate = "60/minute"

    def get_identity(self, request: Request, view) -> str | None:
        ip = ClientIP.get(request)
        return f"ip:{ip}" if ip else None
