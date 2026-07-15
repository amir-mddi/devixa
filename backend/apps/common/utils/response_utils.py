# from __future__ import annotations
#
# from typing import Optional, Any, Mapping, Sequence, TypeVar, cast
# import json
#
# import requests
#
#
# T = TypeVar("T")
#
#
# class ResponseUtils:
#     # -------------------------
#     # Basic helpers
#     # -------------------------
#
#     @staticmethod
#     def content_type(resp: requests.Response) -> str:
#         if resp is None:
#             return ""
#         return (resp.headers.get("Content-Type") or "").lower()
#
#     @staticmethod
#     def short_body(resp: requests.Response, limit: int = 800) -> str:
#         """
#         Safely returns a short body snippet for logging/errors.
#         Works even if response is binary.
#         """
#         if resp is None:
#             return "<no response>"
#
#         try:
#             # Prefer text (requests will decode using apparent encoding)
#             text = resp.text or ""
#         except Exception:
#             try:
#                 raw = resp.content or b""
#                 text = raw[:limit].decode("utf-8", errors="replace")
#             except Exception:
#                 return "<unreadable body>"
#
#         text = text.strip()
#         if len(text) <= limit:
#             return text
#         return text[:limit] + "...(truncated)"
#
#     @staticmethod
#     def has_body(resp: requests.Response) -> bool:
#         if resp is None:
#             return False
#         if resp.status_code == 204:  # No Content
#             return False
#         if resp.content and len(resp.content) > 0:
#             return True
#         return bool(resp.text and resp.text.strip())
#
#     @staticmethod
#     def is_success_2xx(resp: requests.Response) -> bool:
#         """
#         Strict success check (APIs usually expect 2xx only).
#         Note: resp.ok is True for 3xx too.
#         """
#         return resp is not None and 200 <= resp.status_code < 300
#
#     # -------------------------
#     # JSON parsing
#     # -------------------------
#
#     @classmethod
#     def try_json(cls, resp: requests.Response) -> Optional[Any]:
#         """
#         Parses JSON if possible. Never raises. Returns None if invalid/non-JSON.
#         """
#         if resp is None:
#             return None
#
#         # If server claims JSON, try that first
#         ct = cls.content_type(resp)
#         looks_json = "json" in ct
#
#         # 1) First attempt: requests built-in json()
#         try:
#             return resp.json()
#         except ValueError:
#             # 2) If content-type isn't JSON, still sometimes APIs send JSON without header
#             # Try manual parsing only if body looks like JSON or content-type hinted it.
#             body = cls.short_body(resp, limit=10_000)  # safe chunk
#             body_strip = body.lstrip()
#             if looks_json or body_strip.startswith("{") or body_strip.startswith("["):
#                 try:
#                     return json.loads(body)
#                 except Exception:
#                     return None
#             return None
#
#     @classmethod
#     def require_json(cls, resp: requests.Response, *, url: str, method: str) -> Any:
#         payload = cls.try_json(resp)
#         if payload is None:
#             raise HTTPRequestError(
#                 "Response is not valid JSON.",
#                 url=url,
#                 method=method,
#                 status_code=getattr(resp, "status_code", None),
#                 response_text=cls.short_body(resp) if resp is not None else None,
#             )
#         return payload
#
#     # -------------------------
#     # Status / errors
#     # -------------------------
#
#     @classmethod
#     def require_ok(cls, resp: requests.Response, *, url: str, method: str) -> requests.Response:
#         """
#         Uses resp.ok => True for 2xx and 3xx.
#         Suitable for websites; for APIs prefer require_success_2xx().
#         """
#         if resp is None:
#             raise HTTPRequestError("No response received.", url=url, method=method)
#
#         if not resp.ok:
#             raise HTTPRequestError(
#                 f"HTTP request failed with status={resp.status_code}.",
#                 url=url,
#                 method=method,
#                 status_code=resp.status_code,
#                 response_text=cls.short_body(resp),
#             )
#         return resp
#
#     @classmethod
#     def require_success_2xx(cls, resp: requests.Response, *, url: str, method: str) -> requests.Response:
#         """
#         Strict API-style success: only 2xx considered success.
#         """
#         if resp is None:
#             raise HTTPRequestError("No response received.", url=url, method=method)
#
#         if not cls.is_success_2xx(resp):
#             raise HTTPRequestError(
#                 f"HTTP request failed (expected 2xx) status={resp.status_code}.",
#                 url=url,
#                 method=method,
#                 status_code=resp.status_code,
#                 response_text=cls.short_body(resp),
#             )
#         return resp
#
#     # -------------------------
#     # Key/data helpers
#     # -------------------------
#
#     @classmethod
#     def has_json_data(cls, resp: requests.Response) -> bool:
#         payload = cls.try_json(resp)
#         if payload is None:
#             return False
#         if isinstance(payload, (dict, list)):
#             return len(payload) > 0
#         return payload is not None
#
#     @classmethod
#     def has_key_data(cls, resp: requests.Response, key: str = "data") -> bool:
#         payload = cls.try_json(resp)
#         if not isinstance(payload, dict):
#             return False
#         return bool(payload.get(key))
#
#     @classmethod
#     def get_key(cls, payload: Any, key: str, default: T | None = None) -> T | None:
#         """
#         Safe dict get with typing.
#         """
#         if not isinstance(payload, dict):
#             return default
#         return cast(Optional[T], payload.get(key, default))
#
#     @classmethod
#     def require_key(cls, resp: requests.Response, key: str = "data", *, url: str, method: str) -> Any:
#         payload = cls.require_json(resp, url=url, method=method)
#         if not isinstance(payload, dict) or payload.get(key) in (None, {}, [], ""):
#             raise HTTPRequestError(
#                 f"Response JSON has no non-empty '{key}' field.",
#                 url=url,
#                 method=method,
#                 status_code=getattr(resp, "status_code", None),
#                 response_text=str(payload)[:800],
#             )
#         return payload[key]
#
#     @staticmethod
#     def require_dict(value: Any, *, url: str, method: str, status_code: int | None = None) -> dict:
#         if not isinstance(value, dict):
#             raise HTTPRequestError(
#                 "Expected a JSON object (dict) but got a different type.",
#                 url=url,
#                 method=method,
#                 status_code=status_code,
#                 response_text=str(value)[:800],
#             )
#         return value
#
#     @staticmethod
#     def require_list(value: Any, *, url: str, method: str, status_code: int | None = None) -> list:
#         if not isinstance(value, list):
#             raise HTTPRequestError(
#                 "Expected a JSON array (list) but got a different type.",
#                 url=url,
#                 method=method,
#                 status_code=status_code,
#                 response_text=str(value)[:800],
#             )
#         return value
#
#     # -------------------------
#     # CoinMarketCap-specific helper (optional but very useful)
#     # -------------------------
#
#     @classmethod
#     def require_cmc_ok(cls, resp: requests.Response, *, url: str, method: str) -> dict:
#         """
#         CoinMarketCap often returns HTTP 200 even on logical errors.
#         Their body includes: {"status": {"error_code": ... , "error_message": ...}, "data": ...}
#         This enforces:
#           - 2xx status
#           - valid JSON dict
#           - status.error_code in (0, None)
#         Returns parsed payload dict.
#         """
#         cls.require_success_2xx(resp, url=url, method=method)
#
#         payload_any = cls.require_json(resp, url=url, method=method)
#         payload = cls.require_dict(payload_any, url=url, method=method, status_code=resp.status_code)
#
#         status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
#         error_code = (status or {}).get("error_code", 0)
#         if error_code not in (0, None):
#             error_message = (status or {}).get("error_message") or "CoinMarketCap logical error"
#             raise HTTPRequestError(
#                 f"CoinMarketCap error_code={error_code}: {error_message}",
#                 url=url,
#                 method=method,
#                 status_code=resp.status_code,
#                 response_text=cls.short_body(resp),
#             )
#
#         return payload
#
#     @classmethod
#     def require_cmc_data(cls, resp: requests.Response, *, url: str, method: str) -> Any:
#         """
#         Convenience: returns payload['data'] after require_cmc_ok().
#         """
#         payload = cls.require_cmc_ok(resp, url=url, method=method)
#         data = payload.get("data")
#         if data in (None, {}, [], ""):
#             raise HTTPRequestError(
#                 "CoinMarketCap response has empty 'data'.",
#                 url=url,
#                 method=method,
#                 status_code=resp.status_code,
#                 response_text=str(payload)[:800],
#             )
#         return data
