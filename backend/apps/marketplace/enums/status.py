from django.db import models


class ModerationStatus(models.TextChoices):
    PENDING = "pending", "در انتظار بررسی"
    PUBLISHED = "published", "منتشرشده"
    REJECTED = "rejected", "ردشده"


class DeliveryMode(models.TextChoices):
    ONLINE = "online", "آنلاین"
    ONSITE = "onsite", "حضوری"
    BOTH = "both", "آنلاین و حضوری"


class OpportunityKind(models.TextChoices):
    TEACHING = "teaching", "استخدام مدرس"
    TECHNICAL = "technical", "خدمات فنی و پشتیبانی"
    OTHER = "other", "سایر همکاری‌ها"


class BookingStatus(models.TextChoices):
    REQUESTED = "requested", "درخواست‌شده"
    CONFIRMED = "confirmed", "تأییدشده"
    CANCELLED = "cancelled", "لغوشده"
    COMPLETED = "completed", "برگزارشده"
