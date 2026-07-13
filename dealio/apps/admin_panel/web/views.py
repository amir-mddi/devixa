from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from rest_framework.exceptions import APIException

from dealio.apps.admin_panel.enums import AdminPanelSectionEnum
from dealio.apps.admin_panel.logic import (
    AdminBotSettingLogic,
    AdminCourseLogic,
    AdminDashboardLogic,
    AdminPanelActionLogic,
    AdminUserLogic,
)
from dealio.apps.admin_panel.value_objects import (
    AdminPanelMessageVO,
    AdminPanelProviderVO,
)
from dealio.apps.admin_panel.web.forms import (
    AdminBotSettingsForm,
    AdminCourseForm,
    AdminCourseLessonForm,
    AdminDiscountForm,
    AdminNotificationForm,
    AdminReceiptReviewForm,
    AdminReviewModerationForm,
    AdminTicketReplyForm,
    AdminUserForm,
)
from dealio.apps.admin_panel.web.mixins import AdminPanelProtectedViewMixin
from dealio.apps.billing.enums import (
    OrderStatusEnum,
    PaymentReceiptStatusEnum,
    PaymentStatusEnum,
)
from dealio.apps.courses.enums import CourseStatusEnum, ReviewStatusEnum
from dealio.apps.telegram_bot.enums.support_enums import BotSupportProviderEnum
from dealio.apps.telegram_bot.models import BotScheduledNotification, BotSupportTicket


class AdminPanelContextMixin:
    template_root = "web/admin_panel"

    def base_context(self, *, active_section: AdminPanelSectionEnum, **extra):
        return {
            "admin_active_section": active_section.value,
            "admin_sections": AdminPanelSectionEnum,
            **extra,
        }

    @staticmethod
    def page(queryset, request, page_size=20):
        return Paginator(queryset, page_size).get_page(request.GET.get("page", 1))

    @staticmethod
    def error_text(exc: Exception) -> str:
        if isinstance(exc, ValidationError):
            return " ".join(exc.messages)
        detail = getattr(exc, "detail", None)
        if detail:
            return str(detail)
        return AdminPanelMessageVO.OPERATION_FAILED.value


class AdminDashboardView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    dashboard_logic_class = AdminDashboardLogic
    action_logic_class = AdminPanelActionLogic

    def get(self, request):
        action_logic = self.action_logic_class()
        context = self.base_context(
            active_section=AdminPanelSectionEnum.DASHBOARD,
            stats=self.dashboard_logic_class().get_stats(),
            recent_tickets=action_logic.list_tickets(status="", provider="", search="")[
                :5
            ],
            pending_receipts=action_logic.list_receipts(
                status=PaymentReceiptStatusEnum.PENDING.value
            )[:5],
            pending_reviews=action_logic.list_reviews(
                status=ReviewStatusEnum.PENDING.value
            )[:5],
            recipient_counts=action_logic.recipient_counts(),
        )
        return render(request, f"{self.template_root}/dashboard.html", context)


class AdminTicketListView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminPanelActionLogic

    def get(self, request):
        filters = {
            "status": request.GET.get("status", "").strip(),
            "provider": request.GET.get("provider", "").strip(),
            "search": request.GET.get("search", "").strip(),
        }
        tickets = self.logic_class().list_tickets(**filters)
        context = self.base_context(
            active_section=AdminPanelSectionEnum.TICKETS,
            tickets_page=self.page(tickets, request),
            filters=filters,
            ticket_statuses=BotSupportTicket.STATUS_CHOICES,
            providers=[
                (BotSupportProviderEnum.WEB.value, "وب"),
                (BotSupportProviderEnum.TELEGRAM.value, "تلگرام"),
                (BotSupportProviderEnum.BALE.value, "بله"),
                (BotSupportProviderEnum.RUBIKA.value, "روبیکا"),
            ],
        )
        return render(request, f"{self.template_root}/tickets.html", context)


class AdminTicketDetailView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminPanelActionLogic

    def get(self, request, ticket_id):
        ticket = self.logic_class().get_ticket(ticket_id)
        return render(
            request,
            f"{self.template_root}/ticket_detail.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.TICKETS,
                ticket=ticket,
                reply_form=AdminTicketReplyForm(),
            ),
        )


class AdminTicketReplyView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminPanelActionLogic

    def post(self, request, ticket_id):
        form = AdminTicketReplyForm(request.POST)
        if form.is_valid():
            try:
                self.logic_class().reply_ticket(
                    actor=request.user,
                    ticket_id=ticket_id,
                    message=form.cleaned_data["message"],
                )
                messages.success(request, AdminPanelMessageVO.TICKET_REPLIED.value)
            except (ValidationError, APIException) as exc:
                messages.error(request, self.error_text(exc))
        else:
            messages.error(request, AdminPanelMessageVO.OPERATION_FAILED.value)
        return redirect("admin_panel:ticket_detail", ticket_id=ticket_id)


class AdminTicketCloseView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminPanelActionLogic

    def post(self, request, ticket_id):
        try:
            self.logic_class().close_ticket(actor=request.user, ticket_id=ticket_id)
            messages.success(request, AdminPanelMessageVO.TICKET_CLOSED.value)
        except (ValidationError, APIException) as exc:
            messages.error(request, self.error_text(exc))
        return redirect("admin_panel:ticket_detail", ticket_id=ticket_id)


class AdminReviewListView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminPanelActionLogic

    def get(self, request):
        status = request.GET.get("status", ReviewStatusEnum.PENDING.value).strip()
        reviews = self.logic_class().list_reviews(status=status)
        return render(
            request,
            f"{self.template_root}/reviews.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.REVIEWS,
                reviews_page=self.page(reviews, request),
                selected_status=status,
                review_statuses=ReviewStatusEnum.choices(),
                moderation_form=AdminReviewModerationForm(),
            ),
        )


class AdminReviewModerateView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminPanelActionLogic

    def post(self, request, review_id):
        form = AdminReviewModerationForm(request.POST)
        if form.is_valid():
            try:
                self.logic_class().moderate_review(
                    actor=request.user,
                    review_id=review_id,
                    status=form.cleaned_data["status"],
                    admin_note=form.cleaned_data["admin_note"],
                )
                messages.success(request, AdminPanelMessageVO.REVIEW_UPDATED.value)
            except (ValidationError, APIException, ValueError) as exc:
                messages.error(request, self.error_text(exc))
        else:
            messages.error(request, AdminPanelMessageVO.OPERATION_FAILED.value)
        return redirect(
            f'{reverse("admin_panel:reviews")}?status={request.POST.get("status", "pending")}'
        )


class AdminBillingView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminPanelActionLogic

    def get(self, request):
        receipt_status = request.GET.get(
            "receipt_status", PaymentReceiptStatusEnum.PENDING.value
        ).strip()
        order_status = request.GET.get("order_status", "").strip()
        payment_status = request.GET.get("payment_status", "").strip()
        logic = self.logic_class()
        context = self.base_context(
            active_section=AdminPanelSectionEnum.BILLING,
            receipts_page=self.page(
                logic.list_receipts(status=receipt_status), request, 12
            ),
            orders=logic.list_orders(status=order_status)[:40],
            payments=logic.list_payments(status=payment_status)[:40],
            receipt_status=receipt_status,
            order_status=order_status,
            payment_status=payment_status,
            receipt_statuses=PaymentReceiptStatusEnum.choices(),
            order_statuses=OrderStatusEnum.choices(),
            payment_statuses=PaymentStatusEnum.choices(),
            receipt_form=AdminReceiptReviewForm(),
        )
        return render(request, f"{self.template_root}/billing.html", context)


class AdminReceiptReviewView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminPanelActionLogic

    def post(self, request, receipt_id):
        form = AdminReceiptReviewForm(request.POST)
        if form.is_valid():
            try:
                self.logic_class().review_receipt(
                    actor=request.user,
                    receipt_id=receipt_id,
                    approve=form.cleaned_data["action"] == "approve",
                    admin_note=form.cleaned_data["admin_note"],
                    transaction_id=form.cleaned_data["transaction_id"],
                )
                messages.success(request, AdminPanelMessageVO.RECEIPT_UPDATED.value)
            except (ValidationError, APIException) as exc:
                messages.error(request, self.error_text(exc))
        else:
            messages.error(request, AdminPanelMessageVO.OPERATION_FAILED.value)
        return redirect("admin_panel:billing")


class AdminReceiptFileView(AdminPanelProtectedViewMixin, View):
    logic_class = AdminPanelActionLogic

    def get(self, request, receipt_id):
        receipt = self.logic_class().get_receipt(receipt_id)
        if not receipt.receipt_file:
            raise Http404
        try:
            return FileResponse(
                receipt.receipt_file.open("rb"),
                as_attachment=False,
                filename=receipt.receipt_file.name.rsplit("/", 1)[-1],
            )
        except FileNotFoundError as exc:
            raise Http404 from exc


class AdminUserListView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminUserLogic

    def get(self, request):
        filters = {
            "search": request.GET.get("search", "").strip(),
            "role_id": request.GET.get("role", "").strip(),
            "active": request.GET.get("active", "").strip(),
        }
        logic = self.logic_class()
        return render(
            request,
            f"{self.template_root}/users.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.USERS,
                users_page=self.page(logic.list_users(**filters), request),
                roles=logic.list_roles(actor=request.user),
                filters=filters,
            ),
        )


class AdminUserCreateView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminUserLogic

    def get(self, request):
        logic = self.logic_class()
        return render(
            request,
            f"{self.template_root}/user_form.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.USERS,
                form=AdminUserForm(
                    roles=logic.list_roles(actor=request.user),
                    require_password=True,
                    allow_staff=request.user.is_superuser,
                ),
                page_title="ایجاد کاربر جدید",
                submit_label="ایجاد کاربر",
            ),
        )

    def post(self, request):
        logic = self.logic_class()
        form = AdminUserForm(
            request.POST,
            roles=logic.list_roles(actor=request.user),
            require_password=True,
            allow_staff=request.user.is_superuser,
        )
        if form.is_valid():
            try:
                logic.create_user(actor=request.user, dto=form.to_create_dto())
                messages.success(request, AdminPanelMessageVO.USER_CREATED.value)
                return redirect("admin_panel:users")
            except ValidationError as exc:
                form.add_domain_errors(exc)
        return render(
            request,
            f"{self.template_root}/user_form.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.USERS,
                form=form,
                page_title="ایجاد کاربر جدید",
                submit_label="ایجاد کاربر",
            ),
            status=400,
        )


class AdminUserEditView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminUserLogic

    def form_initial(self, user):
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number or "",
            "role_id": str(user.role_id),
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "email_verified": user.email_verified,
            "phone_number_verified": user.phone_number_verified,
        }

    def get(self, request, user_id):
        logic = self.logic_class()
        user = logic.get_user(user_id, actor=request.user)
        return render(
            request,
            f"{self.template_root}/user_form.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.USERS,
                form=AdminUserForm(
                    initial=self.form_initial(user),
                    roles=logic.list_roles(actor=request.user),
                    allow_staff=request.user.is_superuser,
                ),
                managed_user=user,
                page_title="ویرایش کاربر",
                submit_label="ذخیره تغییرات",
            ),
        )

    def post(self, request, user_id):
        logic = self.logic_class()
        user = logic.get_user(user_id, actor=request.user)
        form = AdminUserForm(
            request.POST,
            roles=logic.list_roles(actor=request.user),
            allow_staff=request.user.is_superuser,
        )
        if form.is_valid():
            try:
                logic.update_user(actor=request.user, dto=form.to_update_dto(user.id))
                messages.success(request, AdminPanelMessageVO.USER_UPDATED.value)
                return redirect("admin_panel:users")
            except ValidationError as exc:
                form.add_domain_errors(exc)
        return render(
            request,
            f"{self.template_root}/user_form.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.USERS,
                form=form,
                managed_user=user,
                page_title="ویرایش کاربر",
                submit_label="ذخیره تغییرات",
            ),
            status=400,
        )


class AdminUserToggleView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminUserLogic

    def post(self, request, user_id):
        try:
            self.logic_class().toggle_user(actor=request.user, user_id=user_id)
            messages.success(request, AdminPanelMessageVO.USER_STATUS_UPDATED.value)
        except ValidationError as exc:
            messages.error(request, self.error_text(exc))
        return redirect("admin_panel:users")


class AdminUserDeleteView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminUserLogic

    def post(self, request, user_id):
        try:
            self.logic_class().delete_user(actor=request.user, user_id=user_id)
            messages.success(request, AdminPanelMessageVO.USER_DELETED.value)
        except ValidationError as exc:
            messages.error(request, self.error_text(exc))
        return redirect("admin_panel:users")


class AdminCourseListView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminCourseLogic

    def get(self, request):
        filters = {
            "search": request.GET.get("search", "").strip(),
            "status": request.GET.get("status", "").strip(),
        }
        courses = self.logic_class().list_courses(filters)
        return render(
            request,
            f"{self.template_root}/courses.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.COURSES,
                courses_page=self.page(courses, request),
                filters=filters,
                course_statuses=CourseStatusEnum.choices(),
            ),
        )


class AdminCourseFormMixin(AdminPanelContextMixin):
    logic_class = AdminCourseLogic

    def render_form(self, request, *, form, course=None, status=200):
        return render(
            request,
            f"{self.template_root}/course_form.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.COURSES,
                form=form,
                course=course,
                lesson_form=AdminCourseLessonForm(),
                page_title="ویرایش دوره" if course else "ایجاد دوره جدید",
                submit_label="ذخیره تغییرات" if course else "ایجاد دوره",
            ),
            status=status,
        )


class AdminCourseCreateView(AdminPanelProtectedViewMixin, AdminCourseFormMixin, View):
    def get(self, request):
        logic = self.logic_class()
        return self.render_form(
            request, form=AdminCourseForm(categories=logic.list_categories())
        )

    def post(self, request):
        logic = self.logic_class()
        form = AdminCourseForm(
            request.POST, request.FILES, categories=logic.list_categories()
        )
        if form.is_valid():
            try:
                data = form.to_domain_data()
                logic.create_course(
                    actor=request.user,
                    data=data,
                    thumbnail=form.cleaned_data["thumbnail"],
                )
                messages.success(request, AdminPanelMessageVO.COURSE_CREATED.value)
                return redirect("admin_panel:courses")
            except (ValidationError, APIException) as exc:
                form.add_error(None, self.error_text(exc))
        return self.render_form(request, form=form, status=400)


class AdminCourseEditView(AdminPanelProtectedViewMixin, AdminCourseFormMixin, View):
    def initial(self, course):
        return {
            "title": course.title,
            "short_description": course.short_description,
            "description": course.description,
            "price": course.price,
            "currency": course.currency,
            "level": course.level,
            "status": course.status,
            "duration_minutes": course.duration_minutes,
            "category_id": str(course.category_id or ""),
            "is_featured": course.is_featured,
        }

    def get(self, request, course_id):
        logic = self.logic_class()
        course = logic.get_course(course_id)
        form = AdminCourseForm(
            initial=self.initial(course), categories=logic.list_categories()
        )
        return self.render_form(request, form=form, course=course)

    def post(self, request, course_id):
        logic = self.logic_class()
        course = logic.get_course(course_id)
        form = AdminCourseForm(
            request.POST, request.FILES, categories=logic.list_categories()
        )
        if form.is_valid():
            try:
                data = form.to_domain_data()
                status = data.pop("status")
                logic.update_course(
                    actor=request.user,
                    course_id=course.id,
                    data=data,
                    thumbnail=form.cleaned_data["thumbnail"],
                )
                if status != course.status:
                    logic.update_status(
                        actor=request.user, course_id=course.id, status=status
                    )
                messages.success(request, AdminPanelMessageVO.COURSE_UPDATED.value)
                return redirect("admin_panel:courses")
            except (ValidationError, APIException) as exc:
                form.add_error(None, self.error_text(exc))
        return self.render_form(request, form=form, course=course, status=400)


class AdminCourseDeleteView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminCourseLogic

    def post(self, request, course_id):
        try:
            self.logic_class().delete_course(actor=request.user, course_id=course_id)
            messages.success(request, AdminPanelMessageVO.COURSE_DELETED.value)
        except (ValidationError, APIException) as exc:
            messages.error(request, self.error_text(exc))
        return redirect("admin_panel:courses")


class AdminCourseLessonCreateView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminCourseLogic

    def post(self, request, course_id):
        form = AdminCourseLessonForm(request.POST)
        if form.is_valid():
            try:
                self.logic_class().create_lesson(
                    actor=request.user,
                    course_id=course_id,
                    data=form.to_domain_data(),
                )
                messages.success(request, AdminPanelMessageVO.LESSON_CREATED.value)
            except (ValidationError, APIException) as exc:
                messages.error(request, self.error_text(exc))
        else:
            messages.error(request, AdminPanelMessageVO.OPERATION_FAILED.value)
        return redirect("admin_panel:course_edit", course_id=course_id)


class AdminDiscountListView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    action_logic_class = AdminPanelActionLogic
    course_logic_class = AdminCourseLogic

    def get(self, request):
        return render(
            request,
            f"{self.template_root}/discounts.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.DISCOUNTS,
                discounts=self.action_logic_class().list_discounts(),
                form=AdminDiscountForm(
                    courses=self.course_logic_class().list_courses({})
                ),
            ),
        )


class AdminDiscountCreateView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    action_logic_class = AdminPanelActionLogic
    course_logic_class = AdminCourseLogic

    def post(self, request):
        form = AdminDiscountForm(
            request.POST, courses=self.course_logic_class().list_courses({})
        )
        if form.is_valid():
            try:
                self.action_logic_class().create_discount(
                    actor=request.user,
                    data=form.to_domain_data(),
                )
                messages.success(request, AdminPanelMessageVO.DISCOUNT_CREATED.value)
            except (ValidationError, APIException) as exc:
                messages.error(request, self.error_text(exc))
        else:
            messages.error(request, AdminPanelMessageVO.OPERATION_FAILED.value)
        return redirect("admin_panel:discounts")


class AdminDiscountDeleteView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminPanelActionLogic

    def post(self, request, discount_id):
        try:
            self.logic_class().delete_discount(
                actor=request.user, discount_id=discount_id
            )
            messages.success(request, AdminPanelMessageVO.DISCOUNT_DELETED.value)
        except (ValidationError, APIException) as exc:
            messages.error(request, self.error_text(exc))
        return redirect("admin_panel:discounts")


class AdminNotificationListView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminPanelActionLogic

    def get(self, request):
        provider = request.GET.get("provider", "").strip()
        status = request.GET.get("status", "").strip()
        logic = self.logic_class()
        return render(
            request,
            f"{self.template_root}/notifications.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.NOTIFICATIONS,
                notifications_page=self.page(
                    logic.list_notifications(provider=provider, status=status),
                    request,
                ),
                recipient_counts=logic.recipient_counts(),
                form=AdminNotificationForm(),
                selected_provider=provider,
                selected_status=status,
                notification_statuses=BotScheduledNotification.STATUS_CHOICES,
            ),
        )


class AdminNotificationCreateView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminPanelActionLogic

    def post(self, request):
        form = AdminNotificationForm(request.POST)
        if form.is_valid():
            dto = form.to_dto()
            try:
                _, sent_now = self.logic_class().create_notification(
                    actor=request.user,
                    provider=dto.provider,
                    message=dto.message,
                    scheduled_at=dto.scheduled_at,
                )
                message = (
                    AdminPanelMessageVO.NOTIFICATION_SENT.value
                    if sent_now
                    else AdminPanelMessageVO.NOTIFICATION_SCHEDULED.value
                )
                messages.success(request, message)
            except (ValidationError, APIException, RuntimeError, ValueError) as exc:
                messages.error(request, self.error_text(exc))
        else:
            messages.error(request, AdminPanelMessageVO.OPERATION_FAILED.value)
        return redirect("admin_panel:notifications")


class AdminBotSettingsView(AdminPanelProtectedViewMixin, AdminPanelContextMixin, View):
    logic_class = AdminBotSettingLogic

    def selected_provider(self, request, logic: AdminBotSettingLogic) -> str:
        requested_provider = request.GET.get("provider", "").strip()
        providers = logic.providers()
        return requested_provider if requested_provider in providers else providers[0]

    def render_page(self, request, *, form=None, status=200):
        logic = self.logic_class()
        provider = self.selected_provider(request, logic)
        provider_data = logic.get_provider_settings(provider)
        form = form or AdminBotSettingsForm(settings_data=provider_data["settings"])
        return render(
            request,
            f"{self.template_root}/bot_settings.html",
            self.base_context(
                active_section=AdminPanelSectionEnum.BOT_SETTINGS,
                selected_provider=provider,
                provider_choices=AdminPanelProviderVO.choices(logic.providers()),
                provider_data=provider_data,
                setting_rows=form.setting_rows(),
                form=form,
            ),
            status=status,
        )

    def get(self, request):
        return self.render_page(request)

    def post(self, request):
        logic = self.logic_class()
        provider = self.selected_provider(request, logic)
        provider_data = logic.get_provider_settings(provider)
        form = AdminBotSettingsForm(
            request.POST,
            settings_data=provider_data["settings"],
        )
        if form.is_valid():
            try:
                logic.update_provider_settings(
                    actor=request.user,
                    provider=provider,
                    values=form.cleaned_settings(),
                )
                messages.success(
                    request, AdminPanelMessageVO.BOT_SETTINGS_UPDATED.value
                )
                return redirect(
                    f'{reverse("admin_panel:bot_settings")}?provider={provider}'
                )
            except (ValidationError, APIException) as exc:
                form.add_domain_errors(exc)
        return self.render_page(request, form=form, status=400)


class AdminBotSettingDeleteView(
    AdminPanelProtectedViewMixin, AdminPanelContextMixin, View
):
    logic_class = AdminBotSettingLogic

    def post(self, request, provider, key):
        try:
            self.logic_class().delete_provider_setting(
                actor=request.user,
                provider=provider,
                key=key,
            )
            messages.success(request, AdminPanelMessageVO.BOT_SETTING_RESET.value)
        except (ValidationError, APIException) as exc:
            messages.error(request, self.error_text(exc))
        return redirect(f'{reverse("admin_panel:bot_settings")}?provider={provider}')
