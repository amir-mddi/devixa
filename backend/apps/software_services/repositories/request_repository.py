from backend.apps.software_services.models import SoftwareProjectRequest


class SoftwareRequestRepository:
    def create(self, *, dto, customer=None):
        return SoftwareProjectRequest.objects.create(
            full_name=dto.full_name, email=dto.email, phone=dto.phone,
            category=dto.category, project_title=dto.project_title,
            description=dto.description, budget=dto.budget,
            timeline=dto.timeline, reference_url=dto.reference_url,
            customer=customer,
        )
