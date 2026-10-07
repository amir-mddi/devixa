from __future__ import annotations

from dataclasses import asdict, dataclass

from backend.apps.shared.vo.project_config_vo import ProjectConfigDefaultVO
from backend.apps.common.utils.network_security import force_https_scheme


@dataclass(frozen=True)
class ProjectConfigDTO:
    name: str
    display_name: str
    slug: str
    description: str
    tagline: str
    email_domain: str
    contact_email: str
    support_email: str
    sales_email: str
    partnership_email: str
    github_url: str
    linkedin_url: str
    telegram_url: str
    bale_url: str
    instagram_url: str
    telegram_bot_url: str
    bale_bot_url: str
    rubika_bot_url: str
    phone: str
    address: str
    working_hours: str

    @property
    def logo_initial(self) -> str:
        source = self.display_name or self.name or ProjectConfigDefaultVO.NAME.value
        return source[:1].upper()

    @property
    def business_email(self) -> str:
        """Return the single public business email with backward-compatible fallbacks."""
        return (
            self.contact_email
            or self.support_email
            or self.sales_email
            or self.partnership_email
        )

    def as_context(self) -> dict[str, str]:
        data = asdict(self)
        data["logo_initial"] = self.logo_initial
        data["business_email"] = self.business_email
        return data

    @classmethod
    def from_model(cls, instance) -> "ProjectConfigDTO":
        return cls(
            name=instance.name,
            display_name=instance.display_name,
            slug=instance.slug,
            description=instance.description,
            tagline=instance.tagline,
            email_domain=instance.email_domain,
            contact_email=instance.contact_email,
            support_email=instance.support_email,
            sales_email=instance.sales_email,
            partnership_email=instance.partnership_email,
            github_url=force_https_scheme(instance.github_url),
            linkedin_url=force_https_scheme(instance.linkedin_url),
            telegram_url=force_https_scheme(instance.telegram_url),
            bale_url=force_https_scheme(instance.bale_url),
            instagram_url=force_https_scheme(instance.instagram_url),
            telegram_bot_url=force_https_scheme(instance.telegram_bot_url),
            bale_bot_url=force_https_scheme(instance.bale_bot_url),
            rubika_bot_url=force_https_scheme(instance.rubika_bot_url),
            phone=instance.phone,
            address=instance.address,
            working_hours=instance.working_hours,
        )
