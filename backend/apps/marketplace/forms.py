"""HTTP-bound input validation for the education marketplace."""
from django import forms
from django.core.exceptions import ValidationError

from .models import Academy, AcademyPhoto, CollaborationProject, MentorProfile, MentorshipOffer, Opportunity
from .value_objects.text import MarketplaceText


class MentorProfileForm(forms.ModelForm):
    class Meta:
        model = MentorProfile
        fields = [
            "display_name", "headline", "bio", "subjects", "experience_years",
            "city", "portfolio_url", "resume",
        ]
        labels = {
            "display_name": "نام نمایشی", "headline": "عنوان تخصصی", "bio": "درباره من",
            "subjects": "درس‌ها و مهارت‌ها", "experience_years": "سال‌های تجربه",
            "city": "شهر", "portfolio_url": "لینک نمونه‌کار", "resume": "رزومه PDF (خصوصی)",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "resume": forms.FileInput(attrs={"accept": "application/pdf"}),
        }

    def clean_resume(self):
        uploaded = self.cleaned_data.get("resume")
        if not uploaded or not hasattr(uploaded, "read"):
            return uploaded
        if uploaded.size > 5 * 1024 * 1024 or not uploaded.name.lower().endswith(".pdf"):
            raise ValidationError(MarketplaceText.INVALID_FILE)
        header = uploaded.read(5)
        uploaded.seek(0)
        if header != b"%PDF-":
            raise ValidationError(MarketplaceText.INVALID_FILE)
        return uploaded


class MentorshipOfferForm(forms.ModelForm):
    class Meta:
        model = MentorshipOffer
        fields = ["title", "subject", "description", "hourly_price", "city", "mode"]
        labels = {
            "title": "عنوان آگهی", "subject": "درس یا تخصص", "description": "شرح خدمات",
            "hourly_price": "قیمت هر ساعت (تومان)", "city": "شهر", "mode": "نوع برگزاری",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class AcademyForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = [
            "name", "category", "description", "programs", "facilities", "city",
            "address", "website", "public_phone",
        ]
        labels = {
            "name": "نام مدرسه یا آموزشگاه", "category": "نوع مجموعه",
            "description": "معرفی مجموعه", "programs": "رشته‌ها و دوره‌ها",
            "facilities": "امکانات", "city": "شهر", "address": "آدرس عمومی",
            "website": "وب‌سایت", "public_phone": "شماره تماس عمومی",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "programs": forms.Textarea(attrs={"rows": 3}),
            "facilities": forms.Textarea(attrs={"rows": 3}),
        }


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ["kind", "title", "subject", "description", "city", "budget", "mode"]
        labels = {
            "kind": "نوع آگهی", "title": "عنوان آگهی", "subject": "درس یا تخصص موردنیاز",
            "description": "شرایط و شرح درخواست", "city": "شهر", "budget": "بودجه (تومان؛ اختیاری)",
            "mode": "نوع همکاری",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class SlotForm(forms.Form):
    starts_at = forms.SplitDateTimeField(
        label="شروع جلسه", widget=forms.SplitDateTimeWidget(
            date_attrs={"type": "date"}, time_attrs={"type": "time"},
        ),
    )
    ends_at = forms.SplitDateTimeField(
        label="پایان جلسه", widget=forms.SplitDateTimeWidget(
            date_attrs={"type": "date"}, time_attrs={"type": "time"},
        ),
    )


class ApplicationForm(forms.Form):
    message = forms.CharField(
        label="پیام درخواست همکاری", max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    share_resume = forms.BooleanField(
        label="اجازه می‌دهم مدیر این مجموعه رزومه من را فقط برای این درخواست دریافت کند.",
        required=False,
    )


class ReviewForm(forms.Form):
    rating = forms.IntegerField(label="امتیاز (۱ تا ۵)", min_value=1, max_value=5)
    comment = forms.CharField(
        label="متن نظر", max_length=2000, widget=forms.Textarea(attrs={"rows": 4}),
    )


class AcademyPhotoForm(forms.ModelForm):
    class Meta:
        model = AcademyPhoto
        fields = ["image", "caption"]
        labels = {"image": "عکس مجموعه", "caption": "توضیح عکس (اختیاری)"}

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image.size > 5 * 1024 * 1024 or getattr(image, "content_type", "") not in {
            "image/jpeg", "image/png", "image/webp",
        }:
            raise ValidationError(MarketplaceText.INVALID_PHOTO)
        return image


class CollaborationProjectForm(forms.ModelForm):
    class Meta:
        model = CollaborationProject
        fields = ["title", "specialty", "description", "city", "mode", "max_members"]
        labels = {"title": "عنوان همکاری", "specialty": "مهارت موردنیاز", "description": "معرفی طرح و نقش همکاران", "city": "شهر (اختیاری)", "mode": "شیوه همکاری", "max_members": "حداکثر اعضا (با احتساب صاحب طرح)"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class CollaborationRequestForm(forms.Form):
    message = forms.CharField(label="معرفی و پیشنهاد همکاری", max_length=1500, widget=forms.Textarea(attrs={"rows": 4}))
