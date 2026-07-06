from dealio.apps.common.utils.common_utils import CommonUtils

from django.db.utils import OperationalError, ProgrammingError

logger = CommonUtils.get_project_logger(__name__)


class InitialAccessCache:
    @staticmethod
    def initial_accesses():
        try:
            from dealio.apps.accounts.models import Role

            rows = (
                Role.objects.filter(
                    is_active=True,
                    is_deleted=False,
                    symbol__isnull=False,
                    accesses__isnull=False,
                    accesses__is_active=True,
                    accesses__is_deleted=False,
                )
                .exclude(symbol="")
                .exclude(accesses__name="")
                .values_list("symbol", "accesses__name")
                .distinct()
            )

            return [
                f"{role_symbol}|{access_name}"
                for role_symbol, access_name in rows
                if role_symbol and access_name
            ]

        except (OperationalError, ProgrammingError):
            logger.exception("Could not load initial accesses from database.")
            return []
