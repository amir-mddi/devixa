from __future__ import annotations

from django import forms

from backend.apps.pages.dtos.contact_dto import ContactMessageDTO
from backend.apps.pages.vo.page_vo import (
    PageWebFieldIdVO,
    PageWebFieldLimitVO,
    PageWebFieldNameVO,
    PageWebFormErrorKeyVO,
    PageWebPlaceholderVO,
    PageWebValidationMessageVO,
    PageWebWidgetAttrVO,
    PageWebWidgetClassVO,
)


class PageWebFormErrorMessageFactory:
    @classmethod
    def char_field_messages(cls) -> dict[str, str]:
        return {
            PageWebFormErrorKeyVO.REQUIRED.value: PageWebValidationMessageVO.REQUIRED.value,
            PageWebFormErrorKeyVO.MAX_LENGTH.value: PageWebValidationMessageVO.MAX_LENGTH.value,
            PageWebFormErrorKeyVO.MIN_LENGTH.value: PageWebValidationMessageVO.MESSAGE_TOO_SHORT.value,
        }

    @classmethod
    def email_field_messages(cls) -> dict[str, str]:
        return {
            **cls.char_field_messages(),
            PageWebFormErrorKeyVO.INVALID.value: PageWebValidationMessageVO.INVALID_EMAIL.value,
        }


class ContactMessageTemplateForm(forms.Form):
    full_name = forms.CharField(
        max_length=PageWebFieldLimitVO.FULL_NAME_MAX_LENGTH,
        error_messages=PageWebFormErrorMessageFactory.char_field_messages(),
        widget=forms.TextInput(
            attrs={
                PageWebWidgetAttrVO.ID.value: PageWebFieldIdVO.FULL_NAME.value,
                PageWebWidgetAttrVO.CLASS.value: PageWebWidgetClassVO.INPUT.value,
                PageWebWidgetAttrVO.PLACEHOLDER.value: PageWebPlaceholderVO.FULL_NAME.value,
            }
        ),
    )
    email = forms.EmailField(
        max_length=PageWebFieldLimitVO.EMAIL_MAX_LENGTH,
        error_messages=PageWebFormErrorMessageFactory.email_field_messages(),
        widget=forms.EmailInput(
            attrs={
                PageWebWidgetAttrVO.ID.value: PageWebFieldIdVO.EMAIL.value,
                PageWebWidgetAttrVO.CLASS.value: PageWebWidgetClassVO.INPUT.value,
                PageWebWidgetAttrVO.PLACEHOLDER.value: PageWebPlaceholderVO.EMAIL.value,
            }
        ),
    )
    topic = forms.CharField(
        max_length=PageWebFieldLimitVO.TOPIC_MAX_LENGTH,
        error_messages=PageWebFormErrorMessageFactory.char_field_messages(),
        widget=forms.TextInput(
            attrs={
                PageWebWidgetAttrVO.ID.value: PageWebFieldIdVO.TOPIC.value,
                PageWebWidgetAttrVO.CLASS.value: PageWebWidgetClassVO.INPUT.value,
                PageWebWidgetAttrVO.PLACEHOLDER.value: PageWebPlaceholderVO.TOPIC.value,
            }
        ),
    )
    message = forms.CharField(
        max_length=PageWebFieldLimitVO.MESSAGE_MAX_LENGTH,
        min_length=PageWebFieldLimitVO.MESSAGE_MIN_LENGTH,
        error_messages=PageWebFormErrorMessageFactory.char_field_messages(),
        widget=forms.Textarea(
            attrs={
                PageWebWidgetAttrVO.ID.value: PageWebFieldIdVO.MESSAGE.value,
                PageWebWidgetAttrVO.CLASS.value: PageWebWidgetClassVO.TEXTAREA.value,
                PageWebWidgetAttrVO.PLACEHOLDER.value: PageWebPlaceholderVO.MESSAGE.value,
                PageWebWidgetAttrVO.ROWS.value: 6,
            }
        ),
    )

    def to_dto(self) -> ContactMessageDTO:
        return ContactMessageDTO(
            full_name=self.cleaned_data[PageWebFieldNameVO.FULL_NAME.value].strip(),
            email=self.cleaned_data[PageWebFieldNameVO.EMAIL.value].strip().lower(),
            topic=self.cleaned_data[PageWebFieldNameVO.TOPIC.value].strip(),
            message=self.cleaned_data[PageWebFieldNameVO.MESSAGE.value].strip(),
        )
