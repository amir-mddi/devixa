from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateSoftwareRequestDTO:
    full_name: str
    email: str
    phone: str
    category: str
    project_title: str
    description: str
    budget: str
    timeline: str
    reference_url: str = ""
