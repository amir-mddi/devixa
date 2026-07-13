from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils.timezone import now
from rest_framework.exceptions import NotFound

from dealio.apps.accounts.models import Role
from dealio.apps.billing.enums import OrderStatusEnum, PaymentReceiptStatusEnum
from dealio.apps.billing.models import Order, PaymentReceipt
from dealio.apps.courses.enums import CourseStatusEnum, ReviewStatusEnum
from dealio.apps.courses.models import Course, CourseCategory, CourseReview
from dealio.apps.telegram_bot.models import (
    BotScheduledNotification,
    BotSupportTicket,
    TelegramProfile,
)

User = get_user_model()


class AdminPanelRepository:
    @staticmethod
    def dashboard_counts() -> dict[str, int]:
        return {
            "users_count": User.objects.filter(is_deleted=False).count(),
            "active_courses_count": Course.objects.filter(
                is_deleted=False,
                is_active=True,
                status=CourseStatusEnum.PUBLISHED.value,
            ).count(),
            "open_tickets_count": BotSupportTicket.objects.filter(
                status=BotSupportTicket.STATUS_OPEN
            ).count(),
            "pending_reviews_count": CourseReview.objects.filter(
                is_deleted=False,
                status=ReviewStatusEnum.PENDING.value,
            ).count(),
            "pending_receipts_count": PaymentReceipt.objects.filter(
                is_deleted=False,
                status=PaymentReceiptStatusEnum.PENDING.value,
            ).count(),
            "pending_orders_count": Order.objects.filter(
                is_deleted=False,
                status=OrderStatusEnum.PENDING.value,
            ).count(),
        }

    @staticmethod
    def list_users(*, search: str = "", role_id: str = "", active: str = ""):
        queryset = User.objects.select_related("role").filter(is_deleted=False)
        normalized_search = (search or "").strip()
        if normalized_search:
            queryset = queryset.filter(
                Q(username__icontains=normalized_search)
                | Q(email__icontains=normalized_search)
                | Q(phone_number__icontains=normalized_search)
                | Q(first_name__icontains=normalized_search)
                | Q(last_name__icontains=normalized_search)
            )
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        if active == "active":
            queryset = queryset.filter(is_active=True)
        elif active == "inactive":
            queryset = queryset.filter(is_active=False)
        return queryset.order_by("-created_at")

    @staticmethod
    def get_user(user_id):
        user = (
            User.objects.select_related("role")
            .filter(
                id=user_id,
                is_deleted=False,
            )
            .first()
        )
        if not user:
            raise NotFound("User not found.")
        return user

    @staticmethod
    def list_roles():
        return Role.objects.filter(is_deleted=False, is_active=True).order_by("name")

    @staticmethod
    def get_role(role_id):
        role = Role.objects.filter(
            id=role_id,
            is_deleted=False,
            is_active=True,
        ).first()
        if not role:
            raise NotFound("Role not found.")
        return role

    @staticmethod
    def username_exists(*, username: str, exclude_user_id=None) -> bool:
        queryset = User.objects.filter(username__iexact=username, is_deleted=False)
        if exclude_user_id:
            queryset = queryset.exclude(id=exclude_user_id)
        return queryset.exists()

    @staticmethod
    def email_exists(*, email: str, exclude_user_id=None) -> bool:
        queryset = User.objects.filter(email__iexact=email, is_deleted=False)
        if exclude_user_id:
            queryset = queryset.exclude(id=exclude_user_id)
        return queryset.exists()

    @staticmethod
    def phone_exists(*, phone_number: str, exclude_user_id=None) -> bool:
        if not phone_number:
            return False
        queryset = User.objects.filter(phone_number=phone_number, is_deleted=False)
        if exclude_user_id:
            queryset = queryset.exclude(id=exclude_user_id)
        return queryset.exists()

    @staticmethod
    @transaction.atomic
    def create_user(*, dto, role):
        user = User.objects.create_user(
            username=dto.username,
            email=dto.email,
            password=dto.password,
            first_name=dto.first_name,
            last_name=dto.last_name,
            phone_number=dto.phone_number,
            role=role,
            is_active=dto.is_active,
            is_staff=dto.is_staff,
            user_created_object=None,
        )
        return user

    @staticmethod
    @transaction.atomic
    def update_user(*, user, dto, role, actor):
        previous_email = (user.email or "").strip().lower()
        previous_phone = user.phone_number
        user.username = dto.username
        user.email = dto.email
        user.first_name = dto.first_name
        user.last_name = dto.last_name
        user.phone_number = dto.phone_number
        user.role = role
        user.is_active = dto.is_active
        user.is_staff = dto.is_staff
        user.email_verified = (
            dto.email_verified if previous_email == dto.email else False
        )
        user.phone_number_verified = (
            dto.phone_number_verified if previous_phone == dto.phone_number else False
        )
        user.user_updated_object = actor
        if dto.new_password:
            user.set_password(dto.new_password)
        user.save()
        return user

    @staticmethod
    def set_user_active(*, user, is_active: bool, actor):
        user.is_active = is_active
        user.user_updated_object = actor
        user.save(update_fields=["is_active", "user_updated_object", "updated_at"])
        return user

    @staticmethod
    def soft_delete_user(*, user, actor):
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = now()
        user.user_updated_object = actor
        user.save(
            update_fields=[
                "is_active",
                "is_deleted",
                "deleted_at",
                "user_updated_object",
                "updated_at",
            ]
        )
        return user

    @staticmethod
    def list_course_categories():
        return CourseCategory.objects.filter(
            is_deleted=False,
            is_active=True,
        ).order_by("position", "title")

    @staticmethod
    def update_course_thumbnail(*, course, thumbnail, actor):
        if thumbnail is not None:
            course.thumbnail = thumbnail
            course.user_updated_object = actor
            course.save(
                update_fields=["thumbnail", "user_updated_object", "updated_at"]
            )
        return course

    @staticmethod
    def list_tickets(*, status: str = "", provider: str = "", search: str = ""):
        queryset = (
            BotSupportTicket.objects.select_related("user", "profile")
            .prefetch_related("messages", "messages__sender_user")
            .annotate(message_count=Count("messages"))
        )
        if status:
            queryset = queryset.filter(status=status)
        if provider:
            queryset = queryset.filter(provider=provider)
        normalized_search = (search or "").strip()
        if normalized_search:
            queryset = queryset.filter(
                Q(subject__icontains=normalized_search)
                | Q(user__username__icontains=normalized_search)
                | Q(user__email__icontains=normalized_search)
                | Q(profile__username__icontains=normalized_search)
                | Q(messages__message__icontains=normalized_search)
            ).distinct()
        return queryset.order_by("-last_message_at")

    @staticmethod
    def get_ticket(ticket_id):
        ticket = (
            BotSupportTicket.objects.select_related("user", "profile", "closed_by")
            .prefetch_related("messages", "messages__sender_user")
            .filter(id=ticket_id)
            .first()
        )
        if not ticket:
            raise NotFound("Support ticket not found.")
        return ticket

    @staticmethod
    def get_receipt(receipt_id):
        receipt = (
            PaymentReceipt.objects.select_related(
                "payment",
                "payment__order",
                "payment__user",
                "user",
                "reviewed_by",
            )
            .prefetch_related("payment__order__items", "payment__order__items__course")
            .filter(id=receipt_id, is_deleted=False)
            .first()
        )
        if not receipt:
            raise NotFound("Payment receipt not found.")
        return receipt

    @staticmethod
    def list_scheduled_notifications(*, provider: str = "", status: str = ""):
        queryset = BotScheduledNotification.objects.select_related("created_by")
        if provider:
            queryset = queryset.filter(provider=provider)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-scheduled_at")

    @staticmethod
    def messenger_recipient_counts() -> dict[str, int]:
        rows = (
            TelegramProfile.objects.filter(
                is_active=True,
                is_verified=True,
                user__isnull=False,
                user__is_active=True,
            )
            .values("messenger_provider")
            .annotate(total=Count("id"))
        )
        counts = {"telegram": 0, "bale": 0, "rubika": 0}
        counts.update({row["messenger_provider"]: row["total"] for row in rows})
        return counts
