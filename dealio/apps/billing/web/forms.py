from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from rest_framework import serializers

from dealio.apps.billing.dtos import PaymentReceiptUploadDTO
from dealio.apps.billing.enums import PaymentProviderEnum, PaymentReceiptSourceEnum
from dealio.apps.billing.vo import (
    BasketWebFieldVO,
    BasketWebPlaceholderVO,
    BasketWebValidationVO,
)
from dealio.apps.common.helpers.validators.security_validators import (
    validate_payment_receipt_file,
)


class BasketDiscountForm(forms.Form):
    code = forms.CharField(
        max_length=60,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": BasketWebPlaceholderVO.DISCOUNT_CODE.value,
                "autocomplete": "off",
                "dir": "ltr",
            }
        ),
        error_messages={"required": BasketWebValidationVO.DISCOUNT_REQUIRED.value},
    )


class BasketPaymentMethodForm(forms.Form):
    provider = forms.ChoiceField(
        choices=((PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.CARD_TO_CARD.value),),
        widget=forms.HiddenInput(),
        initial=PaymentProviderEnum.CARD_TO_CARD.value,
    )


class PaymentReceiptUploadTemplateForm(forms.Form):
    receipt_file = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": "image/jpeg,image/png,application/pdf",
                "data-receipt-input": "",
            }
        ),
    )
    tracking_code = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "placeholder": BasketWebPlaceholderVO.TRACKING_CODE.value,
                "dir": "ltr",
            }
        ),
    )
    payer_card_last4 = forms.CharField(
        required=False,
        max_length=4,
        widget=forms.TextInput(
            attrs={
                "placeholder": BasketWebPlaceholderVO.CARD_LAST4.value,
                "inputmode": "numeric",
                "dir": "ltr",
            }
        ),
    )
    paid_amount = forms.DecimalField(
        required=False,
        min_value=Decimal("1"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "placeholder": BasketWebPlaceholderVO.PAID_AMOUNT.value,
                "inputmode": "decimal",
                "dir": "ltr",
            }
        ),
    )
    note = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "placeholder": BasketWebPlaceholderVO.NOTE.value,
                "rows": 3,
            }
        ),
    )

    def clean_receipt_file(self):
        uploaded_file = self.cleaned_data.get(BasketWebFieldVO.RECEIPT_FILE.value)
        if not uploaded_file:
            return None
        try:
            return validate_payment_receipt_file(uploaded_file)
        except serializers.ValidationError as exc:
            raise ValidationError(BasketWebValidationVO.INVALID_RECEIPT.value) from exc

    def clean_tracking_code(self) -> str:
        return str(
            self.cleaned_data.get(BasketWebFieldVO.TRACKING_CODE.value) or ""
        ).strip()

    def clean_payer_card_last4(self) -> str:
        value = str(
            self.cleaned_data.get(BasketWebFieldVO.PAYER_CARD_LAST4.value) or ""
        ).strip()
        if value and (len(value) != 4 or not value.isdigit()):
            raise ValidationError(BasketWebValidationVO.INVALID_CARD_LAST4.value)
        return value

    def clean_note(self) -> str:
        return str(self.cleaned_data.get(BasketWebFieldVO.NOTE.value) or "").strip()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get(BasketWebFieldVO.RECEIPT_FILE.value) and not cleaned_data.get(
            BasketWebFieldVO.TRACKING_CODE.value
        ):
            raise ValidationError(BasketWebValidationVO.RECEIPT_REQUIRED.value)
        return cleaned_data

    def to_dto(self, *, payment_id) -> PaymentReceiptUploadDTO:
        return PaymentReceiptUploadDTO(
            payment_id=payment_id,
            receipt_file=self.cleaned_data.get(BasketWebFieldVO.RECEIPT_FILE.value),
            tracking_code=self.cleaned_data.get(BasketWebFieldVO.TRACKING_CODE.value, ""),
            payer_card_last4=self.cleaned_data.get(BasketWebFieldVO.PAYER_CARD_LAST4.value, ""),
            paid_amount=self.cleaned_data.get(BasketWebFieldVO.PAID_AMOUNT.value),
            note=self.cleaned_data.get(BasketWebFieldVO.NOTE.value, ""),
            source=PaymentReceiptSourceEnum.WEB,
        )
