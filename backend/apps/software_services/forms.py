import re
from django import forms
from backend.apps.software_services.dtos.request_dto import CreateSoftwareRequestDTO
from backend.apps.software_services.enums.request_enums import (
    ProjectBudget, ProjectTimeline, ServiceCategory,
)
from backend.apps.software_services.value_objects.request_vo import SoftwareRequestMessageVO


class SoftwareProjectRequestForm(forms.Form):
    full_name = forms.CharField(max_length=120, label="نام و نام خانوادگی", widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "نام شما"}))
    email = forms.EmailField(label="ایمیل", widget=forms.EmailInput(attrs={"autocomplete": "email", "dir": "ltr", "placeholder": "name@example.com"}))
    phone = forms.CharField(max_length=32, label="شماره تماس", widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "dir": "ltr", "placeholder": "09xxxxxxxxx"}))
    category = forms.ChoiceField(choices=ServiceCategory.choices, label="نوع خدمات")
    project_title = forms.CharField(max_length=180, label="نام پروژه", widget=forms.TextInput(attrs={"placeholder": "مثلاً فروشگاه اینترنتی محصولات من"}))
    description = forms.CharField(min_length=20, max_length=6000, widget=forms.Textarea(attrs={"rows": 5, "placeholder": "ایده، مخاطبان و امکانات موردنیاز پروژه‌تان را توضیح دهید..."}), label="شرح پروژه")
    budget = forms.ChoiceField(choices=ProjectBudget.choices, label="بودجه تقریبی")
    timeline = forms.ChoiceField(choices=ProjectTimeline.choices, label="زمان مورد انتظار")
    reference_url = forms.URLField(required=False, label="لینک نمونه یا مرجع (اختیاری)", widget=forms.URLInput(attrs={"dir": "ltr", "placeholder": "https://example.com"}))
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}), label="")

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError(SoftwareRequestMessageVO.BOT_DETECTED.value)
        return ""

    def clean_phone(self):
        value = self.cleaned_data["phone"].strip()
        # Supports international +98 and domestic phone formats without enforcing Iranian-only leads.
        if not re.fullmatch(r"\+?[0-9۰-۹٠-٩ ()-]{7,32}", value):
            raise forms.ValidationError(SoftwareRequestMessageVO.INVALID_PHONE.value)
        return value

    def clean_reference_url(self):
        value = self.cleaned_data.get("reference_url", "").strip()
        if value and not value.lower().startswith("https://"):
            raise forms.ValidationError(SoftwareRequestMessageVO.INVALID_REFERENCE_URL.value)
        return value

    def to_dto(self):
        return CreateSoftwareRequestDTO(**{
            key: self.cleaned_data[key]
            for key in CreateSoftwareRequestDTO.__dataclass_fields__
        })
