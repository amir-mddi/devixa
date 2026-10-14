from django.db import models


class ServiceCategory(models.TextChoices):
    WEBSITE = "website", "طراحی سایت"
    WEBAPP = "webapp", "وب‌اپلیکیشن"
    MOBILE = "mobile", "اپلیکیشن موبایل"
    TELEGRAM = "telegram", "ربات و اتوماسیون"
    BACKEND = "backend", "بک‌اند و API"
    UIUX = "uiux", "رابط کاربری و تجربه کاربری"
    OTHER = "other", "سایر خدمات فنی"


class ProjectBudget(models.TextChoices):
    UNDECIDED = "undecided", "نیاز به مشاوره"
    SMALL = "small", "کمتر از ۲۰ میلیون تومان"
    MEDIUM = "medium", "۲۰ تا ۶۰ میلیون تومان"
    LARGE = "large", "۶۰ تا ۱۵۰ میلیون تومان"
    ENTERPRISE = "enterprise", "بیشتر از ۱۵۰ میلیون تومان"


class ProjectTimeline(models.TextChoices):
    FLEXIBLE = "flexible", "زمان‌بندی منعطف"
    ONE_MONTH = "one_month", "تا یک ماه"
    THREE_MONTHS = "three_months", "۱ تا ۳ ماه"
    LONG_TERM = "long_term", "بیش از ۳ ماه"


class RequestStatus(models.TextChoices):
    NEW = "new", "جدید"
    CONTACTED = "contacted", "تماس گرفته شده"
    PROPOSAL = "proposal", "پیشنهاد ارسال شده"
    IN_PROGRESS = "in_progress", "در حال انجام"
    COMPLETED = "completed", "تکمیل شده"
    DECLINED = "declined", "بسته شده"
