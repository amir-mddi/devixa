from __future__ import annotations

from django.db import IntegrityError, transaction

from dealio.apps.accounts.dtos.profile_dto import (
    AccountProfileUpdateResultDTO,
    UpdateAccountContactDTO,
    UpdateAccountProfileDTO,
)
from dealio.apps.accounts.entities.profile_entity import AccountProfileEntity
from dealio.apps.accounts.enums.profile_enums import AccountProfileErrorCodeEnum
from dealio.apps.accounts.repositories.adapters.email_adapter import AccountEmailAdapter
from dealio.apps.accounts.repositories.adapters.verification_code_cache_adapter import (
    VerificationCodeCacheAdapter,
)
from dealio.apps.accounts.repositories.profile_repository import (
    AccountProfileRepository,
)
from dealio.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationCacheVO,
)
from dealio.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class AccountProfileLogic:
    def __init__(
        self,
        repository: AccountProfileRepository | None = None,
        email_adapter: AccountEmailAdapter | None = None,
        verification_cache: VerificationCodeCacheAdapter | None = None,
    ):
        self.repository = repository or AccountProfileRepository()
        self.email_adapter = email_adapter or AccountEmailAdapter()
        self.verification_cache = verification_cache or VerificationCodeCacheAdapter()

    def get_profile(self, user_id: str) -> AccountProfileEntity | None:
        user = self.repository.get_user(user_id)
        if not user:
            return None
        return AccountProfileEntity.from_user(user)

    @transaction.atomic
    def update_profile(self, dto: UpdateAccountProfileDTO) -> AccountProfileUpdateResultDTO:
        user = self.repository.get_user(dto.user_id)
        validation_error = self._validate_user(user)
        if validation_error:
            return AccountProfileUpdateResultDTO.failed(error_code=validation_error)

        if self.repository.username_is_used_by_other_user(
            username=dto.username,
            user_id=dto.user_id,
        ):
            return AccountProfileUpdateResultDTO.failed(
                error_code=AccountProfileErrorCodeEnum.USERNAME_ALREADY_IN_USE,
            )

        old_photo = getattr(user, "profile_photo", None)
        old_photo_name = getattr(old_photo, "name", "") if old_photo else ""
        old_photo_storage = getattr(old_photo, "storage", None) if old_photo else None
        replacing_photo = dto.remove_profile_photo or dto.profile_photo is not None

        try:
            # The savepoint protects against a race between the uniqueness check
            # and the database constraint without breaking the outer transaction.
            with transaction.atomic():
                updated_user = self.repository.update_identity(
                    user=user,
                    first_name=dto.first_name,
                    last_name=dto.last_name,
                    username=dto.username,
                    profile_photo=dto.profile_photo,
                    remove_profile_photo=dto.remove_profile_photo,
                )
        except IntegrityError:
            if self.repository.username_is_used_by_other_user(
                username=dto.username,
                user_id=dto.user_id,
            ):
                return AccountProfileUpdateResultDTO.failed(
                    error_code=AccountProfileErrorCodeEnum.USERNAME_ALREADY_IN_USE,
                )
            logger.exception("Profile identity update failed because of an integrity constraint.")
            raise

        if replacing_photo and old_photo_name:
            new_photo_name = getattr(getattr(updated_user, "profile_photo", None), "name", "")
            if old_photo_name != new_photo_name and old_photo_storage:
                transaction.on_commit(
                    lambda storage=old_photo_storage, name=old_photo_name: storage.delete(name)
                )

        return AccountProfileUpdateResultDTO.success(user=updated_user)

    @transaction.atomic
    def update_contacts(self, dto: UpdateAccountContactDTO) -> AccountProfileUpdateResultDTO:
        user = self.repository.get_user(dto.user_id)
        validation_error = self._validate_user(user)
        if validation_error:
            return AccountProfileUpdateResultDTO.failed(error_code=validation_error)

        duplicate_error = self._get_contact_duplicate_error(dto)
        if duplicate_error:
            return AccountProfileUpdateResultDTO.failed(error_code=duplicate_error)

        old_email = user.email
        old_phone_number = user.phone_number or ""
        email_changed = old_email.strip().lower() != dto.email.strip().lower()
        phone_number_changed = old_phone_number != (dto.phone_number or "")

        try:
            with transaction.atomic():
                updated_user = self.repository.update_contacts(
                    user=user,
                    email=dto.email,
                    phone_number=dto.phone_number,
                )
        except IntegrityError:
            duplicate_error = self._get_contact_duplicate_error(dto)
            if duplicate_error:
                return AccountProfileUpdateResultDTO.failed(error_code=duplicate_error)
            logger.exception("Profile contact update failed because of an integrity constraint.")
            raise

        self._clear_previous_verification_codes(
            user_id=str(user.id),
            old_email=old_email,
            old_phone_number=old_phone_number,
            email_changed=email_changed,
            phone_number_changed=phone_number_changed,
        )

        return AccountProfileUpdateResultDTO.success(
            user=updated_user,
            email_changed=email_changed,
            phone_number_changed=phone_number_changed,
        )

    def _get_contact_duplicate_error(
        self,
        dto: UpdateAccountContactDTO,
    ) -> AccountProfileErrorCodeEnum | None:
        if self.repository.email_is_used_by_other_user(
            email=dto.email,
            user_id=dto.user_id,
        ):
            return AccountProfileErrorCodeEnum.EMAIL_ALREADY_IN_USE
        if dto.phone_number and self.repository.phone_number_is_used_by_other_user(
            phone_number=dto.phone_number,
            user_id=dto.user_id,
        ):
            return AccountProfileErrorCodeEnum.PHONE_NUMBER_ALREADY_IN_USE
        return None

    def _clear_previous_verification_codes(
        self,
        *,
        user_id: str,
        old_email: str,
        old_phone_number: str,
        email_changed: bool,
        phone_number_changed: bool,
    ) -> None:
        if email_changed and old_email:
            self.verification_cache.delete_code(
                cache_key=self.email_adapter.get_email_verification_cache_key(
                    user_id,
                    old_email,
                )
            )
        if phone_number_changed and old_phone_number:
            self.verification_cache.delete_code(
                cache_key=AccountPhoneVerificationCacheVO.KEY_TEMPLATE.value.format(
                    user_id=user_id,
                    identifier_fingerprint=self.verification_cache.fingerprint_identifier(
                        old_phone_number
                    ),
                )
            )

    @staticmethod
    def _validate_user(user) -> AccountProfileErrorCodeEnum | None:
        if not user:
            return AccountProfileErrorCodeEnum.USER_NOT_FOUND
        if not user.is_active or getattr(user, "is_deleted", False):
            return AccountProfileErrorCodeEnum.INACTIVE_ACCOUNT
        return None
