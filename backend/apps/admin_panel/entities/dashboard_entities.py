from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdminDashboardStatsEntity:
    users_count: int
    active_courses_count: int
    open_tickets_count: int
    pending_reviews_count: int
    pending_receipts_count: int
    pending_orders_count: int
