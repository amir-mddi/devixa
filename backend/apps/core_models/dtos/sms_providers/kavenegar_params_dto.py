from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KavenegarTemplateSmsDTO:
    recipient_phone_number: str
    template_name: str
    token: str | None = None
    token2: str | None = None
    token3: str | None = None
    token10: str | None = None
    token20: str | None = None