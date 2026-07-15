from __future__ import annotations

from decimal import Decimal
from itertools import count
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone

from backend.apps.accounts.models import Access, Role
from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.articles.models import Article, ArticleCategory, ArticleTag
from backend.apps.billing.enums import PaymentProviderEnum
from backend.apps.billing.models import Order, OrderItem, Payment, PaymentReceipt
from backend.apps.courses.enums import CourseStatusEnum, ReviewStatusEnum
from backend.apps.courses.models import (
    Course,
    CourseCategory,
    CourseEnrollment,
    CourseLesson,
    CourseReview,
)
from backend.apps.shared.models import ProjectConfigModel
from backend.apps.telegram_bot.models import (
    BotRuntimeSetting,
    BotSupportTicket,
    TelegramProfile,
)

User = get_user_model()
_sequence = count(1)


def unique(prefix: str) -> str:
    return f"{prefix}-{next(_sequence)}"


class AccessFactory:
    @classmethod
    def create(cls, **overrides: Any) -> Access:
        values = {"name": unique("access")}
        values.update(overrides)
        return Access.objects.create(**values)


class RoleFactory:
    @classmethod
    def create(cls, **overrides: Any) -> Role:
        accesses = overrides.pop("accesses", ())
        values = {
            "name": unique("role")[:20],
            "symbol": unique("symbol")[:20],
        }
        values.update(overrides)
        role = Role.objects.create(**values)
        if accesses:
            role.accesses.set(accesses)
        return role


class UserFactory:
    DEFAULT_PASSWORD = "StrongPass123!"

    @classmethod
    def create(cls, **overrides: Any):
        password = overrides.pop("password", cls.DEFAULT_PASSWORD)
        role = overrides.pop("role", None) or RoleFactory.create()
        seq = next(_sequence)
        values = {
            "username": f"user{seq}",
            "email": f"user{seq}@gmail.com",
            "first_name": "علی",
            "last_name": "رضایی",
            "role": role,
            "is_active": True,
        }
        values.update(overrides)
        return User.objects.create_user(password=password, **values)

    @classmethod
    def create_admin(cls, **overrides: Any):
        overrides.setdefault("is_staff", True)
        overrides.setdefault("is_superuser", True)
        return cls.create(**overrides)


class ArticleCategoryFactory:
    @classmethod
    def create(cls, **overrides: Any) -> ArticleCategory:
        seq = next(_sequence)
        values = {"title": f"Article Category {seq}", "slug": f"article-category-{seq}"}
        values.update(overrides)
        return ArticleCategory.objects.create(**values)


class ArticleTagFactory:
    @classmethod
    def create(cls, **overrides: Any) -> ArticleTag:
        seq = next(_sequence)
        values = {"title": f"Article Tag {seq}", "slug": f"article-tag-{seq}"}
        values.update(overrides)
        return ArticleTag.objects.create(**values)


class ArticleFactory:
    @classmethod
    def create(cls, **overrides: Any) -> Article:
        seq = next(_sequence)
        values = {
            "author": overrides.pop("author", None) or UserFactory.create(),
            "category": overrides.pop("category", None),
            "article_type": ArticleTypeEnum.BLOG.value,
            "status": ArticleStatusEnum.PUBLISHED.value,
            "title": f"Article {seq}",
            "slug": f"article-{seq}",
            "excerpt": "A useful article excerpt.",
            "content": "A useful article body with enough words for testing.",
        }
        values.update(overrides)
        return Article.objects.create(**values)


class CourseCategoryFactory:
    @classmethod
    def create(cls, **overrides: Any) -> CourseCategory:
        seq = next(_sequence)
        values = {"title": f"Category {seq}", "slug": f"category-{seq}"}
        values.update(overrides)
        return CourseCategory.objects.create(**values)


class CourseFactory:
    @classmethod
    def create(cls, **overrides: Any) -> Course:
        seq = next(_sequence)
        values = {
            "instructor": overrides.pop("instructor", None) or UserFactory.create(),
            "category": overrides.pop("category", None),
            "title": f"Course {seq}",
            "slug": f"course-{seq}",
            "price": Decimal("100000.00"),
            "status": CourseStatusEnum.PUBLISHED.value,
        }
        values.update(overrides)
        return Course.objects.create(**values)


class CourseLessonFactory:
    @classmethod
    def create(cls, **overrides: Any) -> CourseLesson:
        course = overrides.pop("course", None) or CourseFactory.create()
        seq = next(_sequence)
        values = {
            "course": course,
            "title": f"Lesson {seq}",
            "slug": f"lesson-{seq}",
            "position": seq,
        }
        values.update(overrides)
        return CourseLesson.objects.create(**values)


class EnrollmentFactory:
    @classmethod
    def create(cls, **overrides: Any) -> CourseEnrollment:
        values = {
            "user": overrides.pop("user", None) or UserFactory.create(),
            "course": overrides.pop("course", None) or CourseFactory.create(),
        }
        values.update(overrides)
        return CourseEnrollment.objects.create(**values)


class ReviewFactory:
    @classmethod
    def create(cls, **overrides: Any) -> CourseReview:
        values = {
            "user": overrides.pop("user", None) or UserFactory.create(),
            "course": overrides.pop("course", None) or CourseFactory.create(),
            "rating": 5,
            "comment": "Excellent course",
            "status": ReviewStatusEnum.APPROVED.value,
        }
        values.update(overrides)
        return CourseReview.objects.create(**values)


class OrderFactory:
    @classmethod
    def create(cls, **overrides: Any) -> Order:
        values = {"user": overrides.pop("user", None) or UserFactory.create()}
        values.update(overrides)
        return Order.objects.create(**values)


class OrderItemFactory:
    @classmethod
    def create(cls, **overrides: Any) -> OrderItem:
        course = overrides.pop("course", None) or CourseFactory.create()
        values = {
            "order": overrides.pop("order", None) or OrderFactory.create(),
            "course": course,
            "course_title": overrides.pop("course_title", ""),
            "unit_price": overrides.pop("unit_price", course.price),
            "quantity": 1,
            "total_price": Decimal("0.00"),
        }
        values.update(overrides)
        return OrderItem.objects.create(**values)


class PaymentFactory:
    @classmethod
    def create(cls, **overrides: Any) -> Payment:
        order = overrides.pop("order", None) or OrderFactory.create()
        values = {
            "order": order,
            "user": overrides.pop("user", None) or order.user,
            "provider": PaymentProviderEnum.CARD_TO_CARD.value,
            "amount": order.total_amount,
        }
        values.update(overrides)
        return Payment.objects.create(**values)


class PaymentReceiptFactory:
    @classmethod
    def create(cls, **overrides: Any) -> PaymentReceipt:
        payment = overrides.pop("payment", None) or PaymentFactory.create()
        values = {
            "payment": payment,
            "user": overrides.pop("user", None) or payment.user,
        }
        values.update(overrides)
        return PaymentReceipt.objects.create(**values)


class ProjectConfigFactory:
    @classmethod
    def create(cls, **overrides: Any) -> ProjectConfigModel:
        values = {
            "name": unique("Project"),
            "display_name": "Devixa",
            "slug": unique("devixa"),
            "description": "Test project configuration",
            "tagline": "Build it well",
            "email_domain": "example.com",
            "contact_email": "contact@example.com",
            "support_email": "support@example.com",
            "sales_email": "sales@example.com",
            "partnership_email": "partners@example.com",
        }
        values.update(overrides)
        singleton_key = values.pop("singleton_key", "default")
        project_config, _ = ProjectConfigModel.objects.update_or_create(
            singleton_key=singleton_key,
            defaults=values,
        )
        return project_config


class TelegramProfileFactory:
    @classmethod
    def create(cls, **overrides: Any) -> TelegramProfile:
        seq = next(_sequence)
        values = {
            "telegram_user_id": str(seq),
            "messenger_provider": "telegram",
            "chat_id": str(1000 + seq),
            "username": f"telegram_user_{seq}",
        }
        values.update(overrides)
        return TelegramProfile.objects.create(**values)


class BotRuntimeSettingFactory:
    @classmethod
    def create(cls, **overrides: Any) -> BotRuntimeSetting:
        values = {
            "provider": "telegram",
            "key": unique("setting"),
            "value": "value",
        }
        values.update(overrides)
        return BotRuntimeSetting.objects.create(**values)


class BotSupportTicketFactory:
    @classmethod
    def create(cls, **overrides: Any) -> BotSupportTicket:
        values = {
            "provider": "telegram",
            "profile": overrides.pop("profile", None) or TelegramProfileFactory.create(),
            "subject": "Support request",
            "last_message_at": timezone.now(),
        }
        values.update(overrides)
        return BotSupportTicket.objects.create(**values)
