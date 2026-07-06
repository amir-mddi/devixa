from __future__ import annotations

from dataclasses import asdict, dataclass

from dealio.apps.shared.vo.project_config_vo import ProjectConfigDefaultVO


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
    instagram_url: str
    telegram_bot_url: str
    bale_bot_url: str
    phone: str
    address: str
    working_hours: str

    @property
    def logo_initial(self) -> str:
        source = self.display_name or self.name or ProjectConfigDefaultVO.NAME.value
        return source[:1].upper()

    def as_context(self) -> dict[str, str]:
        data = asdict(self)
        data["logo_initial"] = self.logo_initial
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
            github_url=instance.github_url,
            linkedin_url=instance.linkedin_url,
            telegram_url=instance.telegram_url,
            instagram_url=instance.instagram_url,
            telegram_bot_url=instance.telegram_bot_url,
            bale_bot_url=instance.bale_bot_url,
            phone=instance.phone,
            address=instance.address,
            working_hours=instance.working_hours,
        )
