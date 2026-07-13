from __future__ import annotations

from dealio.apps.accounts.repositories.adapters.profile_postgres_adapter import (
    AccountProfilePostgresAdapter,
)


class AccountProfileRepository:
    def __init__(self, adapter: AccountProfilePostgresAdapter | None = None):
        self.adapter = adapter or AccountProfilePostgresAdapter()

    def get_user(self, user_id):
        return self.adapter.get_user(user_id)

    def username_is_used_by_other_user(self, *, username: str, user_id: str) -> bool:
        return self.adapter.username_is_used_by_other_user(
            username=username, user_id=user_id
        )

    def email_is_used_by_other_user(self, *, email: str, user_id: str) -> bool:
        return self.adapter.email_is_used_by_other_user(email=email, user_id=user_id)

    def phone_number_is_used_by_other_user(
        self, *, phone_number: str, user_id: str
    ) -> bool:
        return self.adapter.phone_number_is_used_by_other_user(
            phone_number=phone_number,
            user_id=user_id,
        )

    def update_identity(self, **kwargs):
        return self.adapter.update_identity(**kwargs)

    def update_contacts(self, **kwargs):
        return self.adapter.update_contacts(**kwargs)
