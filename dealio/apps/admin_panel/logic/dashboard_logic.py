from dealio.apps.admin_panel.entities import AdminDashboardStatsEntity
from dealio.apps.admin_panel.repositories import AdminPanelRepository


class AdminDashboardLogic:
    def __init__(self, repository: AdminPanelRepository | None = None):
        self.repository = repository or AdminPanelRepository()

    def get_stats(self) -> AdminDashboardStatsEntity:
        return AdminDashboardStatsEntity(**self.repository.dashboard_counts())
