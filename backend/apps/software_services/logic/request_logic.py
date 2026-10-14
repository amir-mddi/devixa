import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from backend.apps.software_services.enums.request_enums import ServiceCategory, ProjectBudget, ProjectTimeline
from backend.apps.software_services.dtos.request_dto import CreateSoftwareRequestDTO
from backend.apps.software_services.repositories.request_repository import SoftwareRequestRepository
from backend.apps.software_services.value_objects.request_vo import SoftwareRequestMessageVO


class CreateSoftwareRequestLogic:
    def __init__(self, repository=None):
        self.repository = repository or SoftwareRequestRepository()

    def execute(self, *, dto: CreateSoftwareRequestDTO, customer=None):
        if not dto.full_name.strip() or not dto.project_title.strip():
            raise ValidationError(SoftwareRequestMessageVO.INVALID_TITLE.value)
        if len(dto.description.strip()) < 20 or len(dto.description) > 6000:
            raise ValidationError(SoftwareRequestMessageVO.INVALID_DETAILS.value)
        try:
            validate_email(dto.email.strip())
        except ValidationError as exc:
            raise ValidationError(SoftwareRequestMessageVO.INVALID_EMAIL.value) from exc
        if not re.fullmatch(r"\+?[0-9۰-۹٠-٩ ()-]{7,32}", dto.phone.strip()):
            raise ValidationError(SoftwareRequestMessageVO.INVALID_PHONE.value)
        if dto.category not in ServiceCategory.values or dto.budget not in ProjectBudget.values or dto.timeline not in ProjectTimeline.values:
            raise ValidationError(SoftwareRequestMessageVO.INVALID_CATEGORY.value)
        if dto.reference_url and not dto.reference_url.lower().startswith("https://"):
            raise ValidationError(SoftwareRequestMessageVO.INVALID_REFERENCE_URL.value)
        clean = CreateSoftwareRequestDTO(
            full_name=dto.full_name.strip(), email=dto.email.strip().lower(),
            phone=dto.phone.strip(), category=dto.category,
            project_title=dto.project_title.strip(), description=dto.description.strip(),
            budget=dto.budget, timeline=dto.timeline,
            reference_url=dto.reference_url.strip(),
        )
        return self.repository.create(dto=clean, customer=customer)
