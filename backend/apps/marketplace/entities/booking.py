from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class BookingRequest:
    slot_id: UUID
    student_id: UUID
    requested_at: datetime
