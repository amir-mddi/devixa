from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HttpErrorDTO:
    code: str
    title: str
    message: str
    status_code: int
    retry_after_seconds: int | None = None
    technical_detail: str = ""
