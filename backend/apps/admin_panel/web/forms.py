from __future__ import annotations

from decimal import Decimal

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from backend.apps.accounts.web.validators import AccountWebInputValidator
from backend.apps.admin_panel.dtos import (
    AdminNotificationDTO,
    AdminUserCreateDTO,
    AdminUserUpdateDTO,
)
from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.billing.enums import CurrencyEnum, DiscountTypeEnum
from backend.apps.common.helpers.validators.security_validators import (
    validate_profile_photo,
)
from backend.apps.courses.enums import (
    CourseLevelEnum,
    CourseStatusEnum,
    ReviewStatusEnum,
)
from backend.apps.telegram_bot.enums.bot_setting_enums import (
    BotSettingProviderEnum,
    BotSettingValueTypeEnum,
)
from backend.apps.telegram_bot.vo.bot_setting_vo import BotSecretMaskVO


class AdminPanelFormMixin:
    def add_domain_errors(self, exc: ValidationError) -> None:
        if hasattr(exc, "message_dict"):
            for field, errors in exc.message_dict.items():
                for error in errors:
                    self.add_error(field if field in self.fields else None, error)
            return
        for error in getattr(exc, "messages", [str(exc)]):
            self.add_error(None, error)


class AdminUserForm(AdminPanelFormMixin, forms.Form):
    first_name = forms.CharField(max_length=150, label="نام")
    last_name = forms.CharField(max_length=150, label="نام خانوادگی")
    username = forms.CharField(max_length=150, label="نام کاربری")
    email = forms.EmailField(max_length=254, label="ایمیل")
    phone_number = forms.CharField(max_length=13, required=False, label="شماره موبایل")
    role_id = forms.ChoiceField(label="نقش")
    is_active = forms.BooleanField(required=False, initial=True, label="حساب فعال باشد")
    is_staff = forms.BooleanField(required=False, label="دسترسی Django staff")
    email_verified = forms.BooleanField(required=False, label="ایمیل تأیید شده")
    phone_number_verified = forms.BooleanField(required=False, label="موبایل تأیید شده")
    password = forms.CharField(
        required=False,
        label="رمز عبور",
        widget=forms.PasswordInput(render_value=False),
    )

    def __init__(
        self, *args, roles=(), require_password=False, allow_staff=False, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.require_password = require_password
        self.fields["role_id"].choices = [(str(role.id), role.name) for role in roles]
        if not allow_staff:
            self.fields.pop("is_staff")
        if require_password:
            self.fields["password"].required = True
            self.fields["password"].help_text = "رمز عبور اولیه کاربر را وارد کنید."
        else:
            self.fields["password"].help_text = (
                "برای حفظ رمز فعلی، این فیلد را خالی بگذارید."
            )

    def clean_first_name(self):
        return AccountWebInputValidator.validate_persian_text(
            self.cleaned_data["first_name"]
        )

    def clean_last_name(self):
        return AccountWebInputValidator.validate_persian_text(
            self.cleaned_data["last_name"]
        )

    def clean_username(self):
        return AccountWebInputValidator.validate_english_username(
            self.cleaned_data["username"]
        )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_phone_number(self):
        return (
            AccountWebInputValidator.validate_phone_number(
                self.cleaned_data.get("phone_number", ""),
                required=False,
            )
            or None
        )

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        if self.require_password and not password:
            raise ValidationError("رمز عبور الزامی است.")
        if password:
            validate_password(password)
        return password

    def to_create_dto(self) -> AdminUserCreateDTO:
        return AdminUserCreateDTO(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            phone_number=self.cleaned_data["phone_number"],
            password=self.cleaned_data["password"],
            role_id=self.cleaned_data["role_id"],
            is_active=self.cleaned_data["is_active"],
            is_staff=self.cleaned_data.get("is_staff", False),
        )

    def to_update_dto(self, user_id) -> AdminUserUpdateDTO:
        return AdminUserUpdateDTO(
            user_id=user_id,
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            phone_number=self.cleaned_data["phone_number"],
            role_id=self.cleaned_data["role_id"],
            is_active=self.cleaned_data["is_active"],
            is_staff=self.cleaned_data.get("is_staff", False),
            email_verified=self.cleaned_data["email_verified"],
            phone_number_verified=self.cleaned_data["phone_number_verified"],
            new_password=self.cleaned_data["password"],
        )


class AdminCourseForm(AdminPanelFormMixin, forms.Form):
    title = forms.CharField(max_length=180, label="عنوان دوره")
    short_description = forms.CharField(
        max_length=300,
        required=False,
        label="توضیح کوتاه",
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    description = forms.CharField(
        required=False,
        label="توضیحات کامل",
        widget=forms.Textarea(attrs={"rows": 7}),
    )
    price = forms.DecimalField(
        min_value=Decimal("0"), max_digits=12, decimal_places=2, label="قیمت"
    )
    currency = forms.ChoiceField(choices=CurrencyEnum.choices(), label="واحد پول")
    level = forms.ChoiceField(choices=CourseLevelEnum.choices(), label="سطح")
    status = forms.ChoiceField(choices=CourseStatusEnum.choices(), label="وضعیت")
    duration_minutes = forms.IntegerField(min_value=0, label="مدت دوره به دقیقه")
    category_id = forms.ChoiceField(required=False, label="دسته‌بندی")
    is_featured = forms.BooleanField(required=False, label="نمایش در دوره‌های ویژه")
    thumbnail = forms.ImageField(required=False, label="تصویر دوره")

    def __init__(self, *args, categories=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_id"].choices = [("", "بدون دسته‌بندی")] + [
            (str(category.id), category.title) for category in categories
        ]

    def clean_thumbnail(self):
        image = self.cleaned_data.get("thumbnail")
        if not image:
            return None
        try:
            return validate_profile_photo(image)
        except Exception as exc:
            raise ValidationError("تصویر دوره معتبر نیست.") from exc

    def to_domain_data(self) -> dict:
        return {
            "title": self.cleaned_data["title"].strip(),
            "short_description": self.cleaned_data["short_description"].strip(),
            "description": self.cleaned_data["description"].strip(),
            "price": self.cleaned_data["price"],
            "currency": self.cleaned_data["currency"],
            "level": self.cleaned_data["level"],
            "status": self.cleaned_data["status"],
            "duration_minutes": self.cleaned_data["duration_minutes"],
            "category_id": self.cleaned_data["category_id"] or None,
            "is_featured": self.cleaned_data["is_featured"],
        }


class AdminArticleForm(AdminPanelFormMixin, forms.Form):
    article_type = forms.ChoiceField(choices=ArticleTypeEnum.choices(), label="نوع مطلب")
    status = forms.ChoiceField(choices=ArticleStatusEnum.choices(), label="وضعیت")
    title = forms.CharField(max_length=220, label="عنوان")
    slug = forms.SlugField(
        max_length=250,
        required=False,
        allow_unicode=True,
        label="نامک",
        help_text="برای ساخت خودکار از عنوان، خالی بگذارید.",
    )
    excerpt = forms.CharField(
        max_length=420,
        required=False,
        label="خلاصه",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    content = forms.CharField(
        label="محتوا",
        widget=forms.Textarea(attrs={"rows": 14}),
    )
    category_id = forms.ChoiceField(required=False, label="دسته‌بندی")
    tag_ids = forms.MultipleChoiceField(
        required=False,
        label="برچسب‌ها",
        widget=forms.SelectMultiple(attrs={"size": 6}),
    )
    cover_image = forms.ImageField(required=False, label="تصویر شاخص")
    is_featured = forms.BooleanField(required=False, label="مطلب ویژه")
    published_at = forms.DateTimeField(
        required=False,
        label="زمان انتشار",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )
    source_name = forms.CharField(max_length=150, required=False, label="نام منبع")
    source_url = forms.URLField(required=False, label="لینک منبع")
    meta_title = forms.CharField(max_length=220, required=False, label="عنوان SEO")
    meta_description = forms.CharField(
        max_length=320,
        required=False,
        label="توضیحات SEO",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, categories=(), tags=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_id"].choices = [("", "بدون دسته‌بندی")] + [
            (str(category.id), category.title) for category in categories
        ]
        self.fields["tag_ids"].choices = [
            (str(tag.id), tag.title) for tag in tags
        ]

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if not image:
            return None
        try:
            return validate_profile_photo(image)
        except Exception as exc:
            raise ValidationError("تصویر شاخص معتبر نیست.") from exc

    def to_domain_data(self) -> dict:
        return {
            "article_type": self.cleaned_data["article_type"],
            "status": self.cleaned_data["status"],
            "title": self.cleaned_data["title"].strip(),
            "slug": self.cleaned_data["slug"].strip(),
            "excerpt": self.cleaned_data["excerpt"].strip(),
            "content": self.cleaned_data["content"].strip(),
            "category_id": self.cleaned_data["category_id"] or None,
            "tag_ids": tuple(self.cleaned_data["tag_ids"]),
            "cover_image": self.cleaned_data["cover_image"],
            "is_featured": self.cleaned_data["is_featured"],
            "published_at": self.cleaned_data["published_at"],
            "source_name": self.cleaned_data["source_name"].strip(),
            "source_url": self.cleaned_data["source_url"].strip(),
            "meta_title": self.cleaned_data["meta_title"].strip(),
            "meta_description": self.cleaned_data["meta_description"].strip(),
        }


class AdminCourseLessonForm(forms.Form):
    title = forms.CharField(max_length=180, label="عنوان جلسه")
    description = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}), label="توضیح"
    )
    content = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 5}), label="محتوا"
    )
    video_url = forms.URLField(required=False, label="لینک ویدئو")
    duration_minutes = forms.IntegerField(min_value=0, initial=0, label="مدت جلسه")
    position = forms.IntegerField(min_value=1, required=False, label="ترتیب")
    is_preview = forms.BooleanField(required=False, label="جلسه پیش‌نمایش")

    def to_domain_data(self) -> dict:
        return dict(self.cleaned_data)


class AdminTicketReplyForm(forms.Form):
    message = forms.CharField(
        max_length=4000,
        label="پاسخ",
        widget=forms.Textarea(
            attrs={"rows": 5, "placeholder": "پاسخ دقیق برای کاربر بنویسید..."}
        ),
    )


class AdminReviewModerationForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (ReviewStatusEnum.APPROVED.value, "تأیید"),
            (ReviewStatusEnum.REJECTED.value, "رد"),
            (ReviewStatusEnum.PENDING.value, "بازگردانی به انتظار"),
        ],
        label="وضعیت",
    )
    admin_note = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="یادداشت مدیر",
    )


class AdminReceiptReviewForm(forms.Form):
    action = forms.ChoiceField(choices=[("approve", "تأیید"), ("reject", "رد")])
    transaction_id = forms.CharField(
        required=False, max_length=255, label="شماره تراکنش"
    )
    admin_note = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="یادداشت مدیر",
    )


class AdminDiscountForm(forms.Form):
    code = forms.CharField(max_length=60, label="کد تخفیف")
    title = forms.CharField(max_length=160, required=False, label="عنوان")
    discount_type = forms.ChoiceField(
        choices=DiscountTypeEnum.choices(), label="نوع تخفیف"
    )
    value = forms.DecimalField(
        min_value=Decimal("0.01"), max_digits=12, decimal_places=2, label="مقدار"
    )
    course_id = forms.ChoiceField(required=False, label="محدوده دوره")
    usage_limit = forms.IntegerField(
        min_value=1, required=False, label="سقف استفاده کل"
    )
    per_user_limit = forms.IntegerField(
        min_value=1, initial=1, label="سقف استفاده هر کاربر"
    )
    max_discount_amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        required=False,
        label="حداکثر مبلغ تخفیف",
    )
    minimum_order_amount = forms.DecimalField(
        min_value=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        initial=0,
        label="حداقل مبلغ سفارش",
    )
    valid_until = forms.DateTimeField(
        required=False,
        label="اعتبار تا",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    def __init__(self, *args, courses=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course_id"].choices = [("", "همه دوره‌ها")] + [
            (str(course.id), course.title) for course in courses
        ]

    def to_domain_data(self) -> dict:
        data = dict(self.cleaned_data)
        data["course_id"] = data["course_id"] or None
        data["code"] = data["code"].strip().upper()
        return data


class AdminNotificationForm(forms.Form):
    provider = forms.ChoiceField(
        choices=[
            (BotSettingProviderEnum.TELEGRAM.value, "تلگرام"),
            (BotSettingProviderEnum.BALE.value, "بله"),
            (BotSettingProviderEnum.RUBIKA.value, "روبیکا"),
        ],
        label="پیام‌رسان",
    )
    message = forms.CharField(
        max_length=3500, label="متن اعلان", widget=forms.Textarea(attrs={"rows": 7})
    )
    scheduled_at = forms.DateTimeField(
        required=False,
        label="زمان ارسال",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    def to_dto(self) -> AdminNotificationDTO:
        return AdminNotificationDTO(**self.cleaned_data)


class AdminBotSettingsForm(AdminPanelFormMixin, forms.Form):
    """Dynamic form generated only from the bot setting allow-list."""

    def __init__(self, *args, settings_data=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = tuple(settings_data)
        for setting in self.settings_data:
            self.fields[setting["key"]] = self._build_field(setting)

    @staticmethod
    def _build_field(setting: dict):
        common = {
            "label": setting["label"],
            "required": bool(setting["required"]),
            "initial": setting["value"],
            "help_text": setting.get("help_text", ""),
        }
        value_type = setting["value_type"]

        if setting["is_secret"]:
            common["widget"] = forms.PasswordInput(
                render_value=True,
                attrs={"autocomplete": "new-password"},
            )
            common["initial"] = BotSecretMaskVO.MASK if setting["is_configured"] else ""
            return forms.CharField(**common)
        if value_type == BotSettingValueTypeEnum.BOOL.value:
            return forms.ChoiceField(
                choices=(("true", "فعال"), ("false", "غیرفعال")),
                **common,
            )
        if value_type == BotSettingValueTypeEnum.INT.value:
            return forms.IntegerField(**common)
        if value_type == BotSettingValueTypeEnum.FLOAT.value:
            return forms.FloatField(**common)
        if value_type == BotSettingValueTypeEnum.URL.value:
            return forms.URLField(**common)
        if value_type == BotSettingValueTypeEnum.CHOICE.value:
            return forms.ChoiceField(
                choices=tuple(
                    (choice, choice) for choice in setting.get("choices", ())
                ),
                **common,
            )
        return forms.CharField(**common)

    def setting_rows(self):
        return tuple(
            {
                "field": self[setting["key"]],
                "setting": setting,
            }
            for setting in self.settings_data
        )

    def cleaned_settings(self) -> dict:
        return {
            setting["key"]: self.cleaned_data.get(setting["key"], "")
            for setting in self.settings_data
        }
