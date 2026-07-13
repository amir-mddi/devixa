from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from rest_framework import serializers

from dealio.apps.accounts.dtos.password_recovery_dto import (
    ResetPasswordDTO,
    SendPasswordRecoveryCodeDTO,
)
from dealio.apps.accounts.dtos.profile_dto import (
    UpdateAccountContactDTO,
    UpdateAccountProfileDTO,
)
from dealio.apps.accounts.dtos.session_auth_dto import (
    LoginUserDTO,
    PasswordValidationUserDTO,
    RegisterUserDTO,
)
from dealio.apps.accounts.web.validators import AccountWebInputValidator
from dealio.apps.accounts.web.value_objects import (
    AccountWebAutocompleteVO,
    AccountWebFieldLimitVO,
    AccountWebFieldNameVO,
    AccountWebFormErrorKeyVO,
    AccountWebMaxLengthMessageVO,
    AccountWebPlaceholderVO,
    AccountWebValidationMessageVO,
    AccountWebWidgetAttrVO,
)
from dealio.apps.common.helpers.validators.security_validators import (
    validate_profile_photo,
)
from dealio.apps.courses.dtos import ReviewCreateDTO
from dealio.apps.billing.web.forms import (
    PaymentReceiptUploadTemplateForm as BillingPaymentReceiptUploadTemplateForm,
)


class AccountWebFormErrorMessageFactory:
    @classmethod
    def char_field_messages(cls) -> dict[str, str]:
        return {
            AccountWebFormErrorKeyVO.REQUIRED.value: AccountWebValidationMessageVO.REQUIRED.value,
            AccountWebFormErrorKeyVO.MAX_LENGTH.value: AccountWebMaxLengthMessageVO.DEFAULT.value,
        }

    @classmethod
    def email_field_messages(cls) -> dict[str, str]:
        return {
            **cls.char_field_messages(),
            AccountWebFormErrorKeyVO.INVALID.value: AccountWebValidationMessageVO.INVALID_EMAIL.value,
        }


class AccountWebFieldFactory:
    @classmethod
    def text_field(
        cls,
        *,
        max_length: int,
        placeholder: AccountWebPlaceholderVO,
        autocomplete: AccountWebAutocompleteVO | None = None,
    ) -> forms.CharField:
        return forms.CharField(
            max_length=max_length,
            error_messages=AccountWebFormErrorMessageFactory.char_field_messages(),
            widget=forms.TextInput(attrs=cls._widget_attrs(placeholder, autocomplete)),
        )

    @classmethod
    def email_field(cls) -> forms.EmailField:
        return forms.EmailField(
            max_length=AccountWebFieldLimitVO.EMAIL_MAX_LENGTH,
            error_messages=AccountWebFormErrorMessageFactory.email_field_messages(),
            widget=forms.EmailInput(
                attrs=cls._widget_attrs(
                    AccountWebPlaceholderVO.EMAIL,
                    AccountWebAutocompleteVO.EMAIL,
                )
            ),
        )

    @classmethod
    def recovery_code_field(cls) -> forms.CharField:
        return forms.CharField(
            max_length=AccountWebFieldLimitVO.RECOVERY_CODE_MAX_LENGTH,
            error_messages=AccountWebFormErrorMessageFactory.char_field_messages(),
            widget=forms.TextInput(
                attrs=cls._widget_attrs(
                    AccountWebPlaceholderVO.RECOVERY_CODE,
                    AccountWebAutocompleteVO.ONE_TIME_CODE,
                )
            ),
        )

    @classmethod
    def password_field(
        cls,
        *,
        placeholder: AccountWebPlaceholderVO,
        autocomplete: AccountWebAutocompleteVO,
    ) -> forms.CharField:
        return forms.CharField(
            error_messages=AccountWebFormErrorMessageFactory.char_field_messages(),
            widget=forms.PasswordInput(
                attrs=cls._widget_attrs(placeholder, autocomplete)
            ),
        )

    @staticmethod
    def _widget_attrs(
        placeholder: AccountWebPlaceholderVO,
        autocomplete: AccountWebAutocompleteVO | None = None,
    ) -> dict[str, str]:
        attrs = {AccountWebWidgetAttrVO.PLACEHOLDER.value: placeholder.value}

        if autocomplete:
            attrs[AccountWebWidgetAttrVO.AUTOCOMPLETE.value] = autocomplete.value

        return attrs


class AccountWebPasswordConfirmMixin:
    password_field_name: AccountWebFieldNameVO
    password_confirm_field_name = AccountWebFieldNameVO.PASSWORD_CONFIRM

    def get_password_validation_user(self, cleaned_data: dict[str, object]):
        return None

    def validate_password_confirmation(self, cleaned_data: dict[str, object]) -> None:
        password = cleaned_data.get(self.password_field_name.value)
        password_confirm = cleaned_data.get(self.password_confirm_field_name.value)

        if password and password_confirm and password != password_confirm:
            self.add_error(
                self.password_confirm_field_name.value,
                AccountWebValidationMessageVO.PASSWORD_MISMATCH.value,
            )

        if password:
            try:
                AccountWebInputValidator.validate_password(
                    str(password),
                    user=self.get_password_validation_user(cleaned_data),
                )
            except ValidationError as exc:
                self.add_error(self.password_field_name.value, exc)


class LoginTemplateForm(forms.Form):
    identifier = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.EMAIL_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.IDENTIFIER,
        autocomplete=AccountWebAutocompleteVO.USERNAME,
    )
    password = AccountWebFieldFactory.password_field(
        placeholder=AccountWebPlaceholderVO.LOGIN_PASSWORD,
        autocomplete=AccountWebAutocompleteVO.CURRENT_PASSWORD,
    )

    def to_dto(self) -> LoginUserDTO:
        return LoginUserDTO(
            identifier=self.cleaned_data[
                AccountWebFieldNameVO.IDENTIFIER.value
            ].strip(),
            password=self.cleaned_data[AccountWebFieldNameVO.PASSWORD.value],
        )


class RegisterTemplateForm(AccountWebPasswordConfirmMixin, forms.Form):
    password_field_name = AccountWebFieldNameVO.PASSWORD

    first_name = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.NAME_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.FIRST_NAME,
    )
    last_name = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.NAME_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.LAST_NAME,
    )
    username = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.USERNAME_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.USERNAME,
        autocomplete=AccountWebAutocompleteVO.USERNAME,
    )
    email = AccountWebFieldFactory.email_field()
    password = AccountWebFieldFactory.password_field(
        placeholder=AccountWebPlaceholderVO.PASSWORD,
        autocomplete=AccountWebAutocompleteVO.NEW_PASSWORD,
    )
    password_confirm = AccountWebFieldFactory.password_field(
        placeholder=AccountWebPlaceholderVO.PASSWORD_CONFIRM,
        autocomplete=AccountWebAutocompleteVO.NEW_PASSWORD,
    )

    def get_password_validation_user(
        self, cleaned_data: dict[str, object]
    ) -> PasswordValidationUserDTO:
        return PasswordValidationUserDTO(
            first_name=str(
                cleaned_data.get(AccountWebFieldNameVO.FIRST_NAME.value) or ""
            ),
            last_name=str(
                cleaned_data.get(AccountWebFieldNameVO.LAST_NAME.value) or ""
            ),
            username=str(cleaned_data.get(AccountWebFieldNameVO.USERNAME.value) or ""),
            email=str(cleaned_data.get(AccountWebFieldNameVO.EMAIL.value) or ""),
        )

    def clean_first_name(self) -> str:
        return AccountWebInputValidator.validate_persian_text(
            self.cleaned_data[AccountWebFieldNameVO.FIRST_NAME.value]
        )

    def clean_last_name(self) -> str:
        return AccountWebInputValidator.validate_persian_text(
            self.cleaned_data[AccountWebFieldNameVO.LAST_NAME.value]
        )

    def clean_username(self) -> str:
        return AccountWebInputValidator.validate_english_username(
            self.cleaned_data[AccountWebFieldNameVO.USERNAME.value]
        )

    def clean_email(self) -> str:
        return AccountWebInputValidator.validate_gmail_email(
            self.cleaned_data[AccountWebFieldNameVO.EMAIL.value]
        )

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        self.validate_password_confirmation(cleaned_data)
        return cleaned_data

    def to_dto(self) -> RegisterUserDTO:
        return RegisterUserDTO(
            first_name=self.cleaned_data[AccountWebFieldNameVO.FIRST_NAME.value],
            last_name=self.cleaned_data[AccountWebFieldNameVO.LAST_NAME.value],
            username=self.cleaned_data[AccountWebFieldNameVO.USERNAME.value],
            email=self.cleaned_data[AccountWebFieldNameVO.EMAIL.value],
            password=self.cleaned_data[AccountWebFieldNameVO.PASSWORD.value],
        )


class ForgotPasswordTemplateForm(forms.Form):
    email = AccountWebFieldFactory.email_field()

    def clean_email(self) -> str:
        return AccountWebInputValidator.validate_gmail_email(
            self.cleaned_data[AccountWebFieldNameVO.EMAIL.value]
        )

    def to_dto(self) -> SendPasswordRecoveryCodeDTO:
        return SendPasswordRecoveryCodeDTO(
            email=self.cleaned_data[AccountWebFieldNameVO.EMAIL.value]
        )


class RecoverPasswordTemplateForm(AccountWebPasswordConfirmMixin, forms.Form):
    password_field_name = AccountWebFieldNameVO.NEW_PASSWORD

    email = AccountWebFieldFactory.email_field()
    code = AccountWebFieldFactory.recovery_code_field()
    new_password = AccountWebFieldFactory.password_field(
        placeholder=AccountWebPlaceholderVO.NEW_PASSWORD,
        autocomplete=AccountWebAutocompleteVO.NEW_PASSWORD,
    )
    password_confirm = AccountWebFieldFactory.password_field(
        placeholder=AccountWebPlaceholderVO.NEW_PASSWORD_CONFIRM,
        autocomplete=AccountWebAutocompleteVO.NEW_PASSWORD,
    )

    def clean_email(self) -> str:
        return AccountWebInputValidator.validate_gmail_email(
            self.cleaned_data[AccountWebFieldNameVO.EMAIL.value]
        )

    def clean_code(self) -> str:
        return AccountWebInputValidator.validate_recovery_code(
            self.cleaned_data[AccountWebFieldNameVO.CODE.value]
        )

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        self.validate_password_confirmation(cleaned_data)
        return cleaned_data

    def to_dto(self) -> ResetPasswordDTO:
        return ResetPasswordDTO(
            email=self.cleaned_data[AccountWebFieldNameVO.EMAIL.value],
            code=self.cleaned_data[AccountWebFieldNameVO.CODE.value],
            new_password=self.cleaned_data[AccountWebFieldNameVO.NEW_PASSWORD.value],
        )


class ProfileIdentityTemplateForm(forms.Form):
    first_name = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.NAME_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.FIRST_NAME,
    )
    last_name = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.NAME_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.LAST_NAME,
    )
    username = AccountWebFieldFactory.text_field(
        max_length=AccountWebFieldLimitVO.USERNAME_MAX_LENGTH,
        placeholder=AccountWebPlaceholderVO.USERNAME,
        autocomplete=AccountWebAutocompleteVO.USERNAME,
    )
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
    )
    remove_profile_photo = forms.BooleanField(required=False)

    def clean_first_name(self) -> str:
        return AccountWebInputValidator.validate_persian_text(
            self.cleaned_data[AccountWebFieldNameVO.FIRST_NAME.value]
        )

    def clean_last_name(self) -> str:
        return AccountWebInputValidator.validate_persian_text(
            self.cleaned_data[AccountWebFieldNameVO.LAST_NAME.value]
        )

    def clean_username(self) -> str:
        return AccountWebInputValidator.validate_english_username(
            self.cleaned_data[AccountWebFieldNameVO.USERNAME.value]
        )

    def clean_profile_photo(self):
        uploaded_file = self.cleaned_data.get(AccountWebFieldNameVO.PROFILE_PHOTO.value)
        if not uploaded_file:
            return None

        try:
            return validate_profile_photo(uploaded_file)
        except serializers.ValidationError as exc:
            raise ValidationError(
                AccountWebValidationMessageVO.INVALID_PROFILE_PHOTO.value
            ) from exc

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        if cleaned_data.get(AccountWebFieldNameVO.PROFILE_PHOTO.value):
            cleaned_data[AccountWebFieldNameVO.REMOVE_PROFILE_PHOTO.value] = False
        return cleaned_data

    def to_dto(self, *, user_id: str) -> UpdateAccountProfileDTO:
        return UpdateAccountProfileDTO(
            user_id=user_id,
            first_name=self.cleaned_data[AccountWebFieldNameVO.FIRST_NAME.value],
            last_name=self.cleaned_data[AccountWebFieldNameVO.LAST_NAME.value],
            username=self.cleaned_data[AccountWebFieldNameVO.USERNAME.value],
            profile_photo=self.cleaned_data.get(
                AccountWebFieldNameVO.PROFILE_PHOTO.value
            ),
            remove_profile_photo=bool(
                self.cleaned_data.get(AccountWebFieldNameVO.REMOVE_PROFILE_PHOTO.value)
            ),
        )


class ProfileContactTemplateForm(forms.Form):
    email = AccountWebFieldFactory.email_field()
    phone_number = forms.CharField(
        required=False,
        max_length=AccountWebFieldLimitVO.PHONE_NUMBER_MAX_LENGTH,
        widget=forms.TextInput(
            attrs={
                AccountWebWidgetAttrVO.PLACEHOLDER.value: AccountWebPlaceholderVO.PHONE_NUMBER.value,
                AccountWebWidgetAttrVO.AUTOCOMPLETE.value: AccountWebAutocompleteVO.TEL.value,
                "inputmode": "tel",
                "dir": "ltr",
            }
        ),
    )

    def clean_email(self) -> str:
        return AccountWebInputValidator.validate_gmail_email(
            self.cleaned_data[AccountWebFieldNameVO.EMAIL.value]
        )

    def clean_phone_number(self) -> str:
        return AccountWebInputValidator.validate_phone_number(
            self.cleaned_data.get(AccountWebFieldNameVO.PHONE_NUMBER.value, ""),
            required=False,
        )

    def to_dto(self, *, user_id: str) -> UpdateAccountContactDTO:
        phone_number = (
            self.cleaned_data.get(AccountWebFieldNameVO.PHONE_NUMBER.value) or None
        )
        return UpdateAccountContactDTO(
            user_id=user_id,
            email=self.cleaned_data[AccountWebFieldNameVO.EMAIL.value],
            phone_number=phone_number,
        )


class VerificationCodeTemplateForm(forms.Form):
    code = AccountWebFieldFactory.recovery_code_field()

    def clean_code(self) -> str:
        return AccountWebInputValidator.validate_recovery_code(
            self.cleaned_data[AccountWebFieldNameVO.CODE.value]
        )


class SupportTicketTemplateForm(forms.Form):
    subject = forms.CharField(
        max_length=AccountWebFieldLimitVO.SUPPORT_SUBJECT_MAX_LENGTH,
        widget=forms.TextInput(
            attrs={
                AccountWebWidgetAttrVO.PLACEHOLDER.value: AccountWebPlaceholderVO.SUPPORT_SUBJECT.value
            }
        ),
    )
    message = forms.CharField(
        max_length=AccountWebFieldLimitVO.SUPPORT_MESSAGE_MAX_LENGTH,
        min_length=3,
        widget=forms.Textarea(
            attrs={
                AccountWebWidgetAttrVO.PLACEHOLDER.value: AccountWebPlaceholderVO.SUPPORT_MESSAGE.value,
                "rows": 5,
            }
        ),
        error_messages={
            AccountWebFormErrorKeyVO.REQUIRED.value: AccountWebValidationMessageVO.REQUIRED.value,
            "min_length": AccountWebValidationMessageVO.SUPPORT_MESSAGE_TOO_SHORT.value,
            AccountWebFormErrorKeyVO.MAX_LENGTH.value: AccountWebMaxLengthMessageVO.DEFAULT.value,
        },
    )


class SupportReplyTemplateForm(forms.Form):
    message = forms.CharField(
        max_length=AccountWebFieldLimitVO.SUPPORT_MESSAGE_MAX_LENGTH,
        min_length=3,
        widget=forms.Textarea(
            attrs={
                AccountWebWidgetAttrVO.PLACEHOLDER.value: AccountWebPlaceholderVO.SUPPORT_MESSAGE.value,
                "rows": 3,
            }
        ),
        error_messages={
            AccountWebFormErrorKeyVO.REQUIRED.value: AccountWebValidationMessageVO.REQUIRED.value,
            "min_length": AccountWebValidationMessageVO.SUPPORT_MESSAGE_TOO_SHORT.value,
            AccountWebFormErrorKeyVO.MAX_LENGTH.value: AccountWebMaxLengthMessageVO.DEFAULT.value,
        },
    )


class CourseReviewTemplateForm(forms.Form):
    rating = forms.TypedChoiceField(
        choices=(
            (5, "۵ ستاره"),
            (4, "۴ ستاره"),
            (3, "۳ ستاره"),
            (2, "۲ ستاره"),
            (1, "۱ ستاره"),
        ),
        coerce=int,
    )
    title = forms.CharField(
        required=False,
        max_length=AccountWebFieldLimitVO.REVIEW_TITLE_MAX_LENGTH,
        widget=forms.TextInput(
            attrs={
                AccountWebWidgetAttrVO.PLACEHOLDER.value: AccountWebPlaceholderVO.REVIEW_TITLE.value
            }
        ),
    )
    comment = forms.CharField(
        min_length=3,
        max_length=AccountWebFieldLimitVO.REVIEW_COMMENT_MAX_LENGTH,
        widget=forms.Textarea(
            attrs={
                AccountWebWidgetAttrVO.PLACEHOLDER.value: AccountWebPlaceholderVO.REVIEW_COMMENT.value,
                "rows": 4,
            }
        ),
        error_messages={
            AccountWebFormErrorKeyVO.REQUIRED.value: AccountWebValidationMessageVO.REQUIRED.value,
            "min_length": AccountWebValidationMessageVO.REVIEW_COMMENT_TOO_SHORT.value,
            AccountWebFormErrorKeyVO.MAX_LENGTH.value: AccountWebMaxLengthMessageVO.DEFAULT.value,
        },
    )

    def to_dto(self, *, course_id) -> ReviewCreateDTO:
        return ReviewCreateDTO(
            course_id=course_id,
            rating=self.cleaned_data[AccountWebFieldNameVO.RATING.value],
            title=(
                self.cleaned_data.get(AccountWebFieldNameVO.TITLE.value) or ""
            ).strip(),
            comment=self.cleaned_data[AccountWebFieldNameVO.COMMENT.value].strip(),
        )




class PaymentReceiptUploadTemplateForm(BillingPaymentReceiptUploadTemplateForm):
    """Backward-compatible account form alias without duplicated receipt logic."""

