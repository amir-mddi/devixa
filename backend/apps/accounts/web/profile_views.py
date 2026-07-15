from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from rest_framework.exceptions import APIException

from backend.apps.accounts.dtos.phone_verification_dto import (
    SendPhoneVerificationCodeDTO,
    VerifyPhoneNumberDTO,
)
from backend.apps.accounts.logic.profile_dashboard_logic import (
    AccountProfileDashboardLogic,
)
from backend.apps.accounts.logic.profile_logic import AccountProfileLogic
from backend.apps.accounts.repositories.account_logic import AccountLogicRepository
from backend.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationApiMessageVO,
)
from backend.apps.accounts.vo.profile_vo import (
    AccountProfileMessageVO,
    AccountProfileSectionVO,
)
from backend.apps.accounts.web.forms import (
    CourseReviewTemplateForm,
    PaymentReceiptUploadTemplateForm,
    ProfileContactTemplateForm,
    ProfileIdentityTemplateForm,
    SupportReplyTemplateForm,
    SupportTicketTemplateForm,
    VerificationCodeTemplateForm,
)
from backend.apps.accounts.web.presenters import AccountWebProfileErrorPresenter
from backend.apps.accounts.web.value_objects import (
    AccountWebReverseNameVO,
    AccountWebTemplateVO,
)
from backend.apps.billing.repositories.logic import BillingLogicRepository
from backend.apps.common.helpers.decorators.rate_limit import rate_limit
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.courses.repositories.logic import CourseLogicRepository
from backend.apps.telegram_bot.dtos.profile_dtos import DisconnectMessengerProfileDTO
from backend.apps.telegram_bot.logic.profile_logic import MessengerProfileLogic
from backend.apps.telegram_bot.repositories.logic.bot_support_logic import (
    BotSupportLogicRepository,
)

logger = CommonUtils.get_project_logger(__name__)


class ProfilePanelContextMixin:
    template_name = AccountWebTemplateVO.PROFILE.value
    dashboard_logic_class = AccountProfileDashboardLogic

    def build_context(self, *, active_section: str, **overrides):
        dashboard = self.dashboard_logic_class().build(self.request.user)
        profile = dashboard.profile
        receipt_upload_forms = {
            str(payment.id): PaymentReceiptUploadTemplateForm(
                prefix=f"receipt-{payment.id}"
            )
            for payment in dashboard.payments
            if payment.id in dashboard.receipt_upload_payment_ids
        }
        receipt_upload_forms.update(overrides.pop("receipt_upload_forms", {}))
        context = {
            "dashboard": dashboard,
            "profile": profile,
            "active_section": active_section,
            "profile_form": ProfileIdentityTemplateForm(
                initial={
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "username": profile.username,
                }
            ),
            "contact_form": ProfileContactTemplateForm(
                initial={
                    "email": profile.email,
                    "phone_number": profile.phone_number,
                }
            ),
            "email_code_form": VerificationCodeTemplateForm(prefix="email"),
            "phone_code_form": VerificationCodeTemplateForm(prefix="phone"),
            "ticket_form": SupportTicketTemplateForm(),
            "receipt_upload_forms": receipt_upload_forms,
        }
        context.update(overrides)
        return context

    def render_panel(self, *, active_section: str, status: int = 200, **overrides):
        return render(
            self.request,
            self.template_name,
            self.build_context(active_section=active_section, **overrides),
            status=status,
        )

    @staticmethod
    def profile_redirect(section: AccountProfileSectionVO):
        return redirect(
            f"{reverse(AccountWebReverseNameVO.PROFILE.value)}#{section.value}"
        )


class ProfileDashboardView(LoginRequiredMixin, ProfilePanelContextMixin, TemplateView):
    template_name = AccountWebTemplateVO.PROFILE.value

    def get_context_data(self, **kwargs):
        return self.build_context(active_section=AccountProfileSectionVO.OVERVIEW.value)


@method_decorator(
    rate_limit(authenticated_limit=8, anonymous_limit=0, period=300), name="post"
)
class ProfileMessengerDisconnectView(
    LoginRequiredMixin, ProfilePanelContextMixin, View
):
    messenger_profile_logic_class = MessengerProfileLogic

    def post(self, request, profile_id, *args, **kwargs):
        result = self.messenger_profile_logic_class().disconnect(
            DisconnectMessengerProfileDTO(
                profile_id=profile_id,
                user_id=request.user.id,
            )
        )
        message = (
            AccountProfileMessageVO.MESSENGER_DISCONNECTED.value
            if result.is_success
            else AccountProfileMessageVO.MESSENGER_DISCONNECT_FAILED.value
        )
        message_method = messages.success if result.is_success else messages.error
        message_method(request, message)
        return self.profile_redirect(AccountProfileSectionVO.OVERVIEW)


@method_decorator(
    rate_limit(authenticated_limit=10, anonymous_limit=0, period=300), name="post"
)
class ProfileIdentityUpdateView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    profile_logic_class = AccountProfileLogic

    def post(self, request, *args, **kwargs):
        form = ProfileIdentityTemplateForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_panel(
                active_section=AccountProfileSectionVO.PROFILE.value,
                profile_form=form,
                status=400,
            )

        result = self.profile_logic_class().update_profile(
            form.to_dto(user_id=str(request.user.id))
        )
        if not result.is_success:
            form.add_error(
                AccountWebProfileErrorPresenter.field_for(result.error_code),
                AccountWebProfileErrorPresenter.message_for(result.error_code),
            )
            return self.render_panel(
                active_section=AccountProfileSectionVO.PROFILE.value,
                profile_form=form,
                status=400,
            )

        messages.success(request, AccountProfileMessageVO.PROFILE_UPDATED.value)
        return self.profile_redirect(AccountProfileSectionVO.PROFILE)


@method_decorator(
    rate_limit(authenticated_limit=10, anonymous_limit=0, period=300), name="post"
)
class ProfileContactUpdateView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    profile_logic_class = AccountProfileLogic

    def post(self, request, *args, **kwargs):
        form = ProfileContactTemplateForm(request.POST)
        if not form.is_valid():
            return self.render_panel(
                active_section=AccountProfileSectionVO.CONTACT.value,
                contact_form=form,
                status=400,
            )

        result = self.profile_logic_class().update_contacts(
            form.to_dto(user_id=str(request.user.id))
        )
        if not result.is_success:
            form.add_error(
                AccountWebProfileErrorPresenter.field_for(result.error_code),
                AccountWebProfileErrorPresenter.message_for(result.error_code),
            )
            return self.render_panel(
                active_section=AccountProfileSectionVO.CONTACT.value,
                contact_form=form,
                status=400,
            )

        messages.success(request, AccountProfileMessageVO.CONTACT_UPDATED.value)
        if result.email_changed:
            messages.info(request, AccountProfileMessageVO.EMAIL_CHANGED_REVERIFY.value)
        if result.phone_number_changed:
            messages.info(request, AccountProfileMessageVO.PHONE_CHANGED_REVERIFY.value)
        return self.profile_redirect(AccountProfileSectionVO.CONTACT)


@method_decorator(
    rate_limit(authenticated_limit=5, anonymous_limit=0, period=300), name="post"
)
class ProfileEmailVerificationSendView(
    LoginRequiredMixin, ProfilePanelContextMixin, View
):
    account_logic_class = AccountLogicRepository

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.email:
            messages.error(request, AccountProfileMessageVO.EMAIL_REQUIRED.value)
        elif user.email_verified:
            messages.info(request, AccountProfileMessageVO.EMAIL_ALREADY_VERIFIED.value)
        else:
            try:
                issued = self.account_logic_class().send_verification_email_code(user)
            except Exception:
                logger.exception(
                    "Sending a profile email verification code failed for user %s.",
                    user.id,
                )
                messages.error(request, AccountProfileMessageVO.EMAIL_SEND_FAILED.value)
            else:
                message = (
                    AccountProfileMessageVO.EMAIL_CODE_SENT.value
                    if issued
                    else AccountProfileMessageVO.EMAIL_CODE_STILL_ACTIVE.value
                )
                messages.success(request, message)
        return self.profile_redirect(AccountProfileSectionVO.CONTACT)


@method_decorator(
    rate_limit(authenticated_limit=10, anonymous_limit=0, period=300), name="post"
)
class ProfileEmailVerificationView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    account_logic_class = AccountLogicRepository

    def post(self, request, *args, **kwargs):
        form = VerificationCodeTemplateForm(request.POST, prefix="email")
        if not form.is_valid():
            return self.render_panel(
                active_section=AccountProfileSectionVO.CONTACT.value,
                email_code_form=form,
                status=400,
            )

        if request.user.email_verified:
            messages.info(request, AccountProfileMessageVO.EMAIL_ALREADY_VERIFIED.value)
        elif self.account_logic_class().check_email_validation_code(
            request.user,
            form.cleaned_data["code"],
        ):
            messages.success(request, AccountProfileMessageVO.EMAIL_VERIFIED.value)
        else:
            form.add_error("code", AccountProfileMessageVO.EMAIL_CODE_INVALID.value)
            return self.render_panel(
                active_section=AccountProfileSectionVO.CONTACT.value,
                email_code_form=form,
                status=400,
            )
        return self.profile_redirect(AccountProfileSectionVO.CONTACT)


@method_decorator(
    rate_limit(authenticated_limit=5, anonymous_limit=0, period=300), name="post"
)
class ProfilePhoneVerificationSendView(
    LoginRequiredMixin, ProfilePanelContextMixin, View
):
    account_logic_class = AccountLogicRepository

    def post(self, request, *args, **kwargs):
        result = self.account_logic_class().send_phone_verification_code(
            SendPhoneVerificationCodeDTO(user_id=str(request.user.id))
        )
        if result.is_success:
            message = (
                AccountPhoneVerificationApiMessageVO.CODE_SENT.value
                if result.code_issued
                else AccountPhoneVerificationApiMessageVO.CODE_STILL_ACTIVE.value
            )
            messages.success(request, message)
        else:
            messages.error(
                request,
                AccountWebProfileErrorPresenter.phone_verification_message_for(
                    result.error_code
                ),
            )
        return self.profile_redirect(AccountProfileSectionVO.CONTACT)


@method_decorator(
    rate_limit(authenticated_limit=10, anonymous_limit=0, period=300), name="post"
)
class ProfilePhoneVerificationView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    account_logic_class = AccountLogicRepository

    def post(self, request, *args, **kwargs):
        form = VerificationCodeTemplateForm(request.POST, prefix="phone")
        if not form.is_valid():
            return self.render_panel(
                active_section=AccountProfileSectionVO.CONTACT.value,
                phone_code_form=form,
                status=400,
            )

        result = self.account_logic_class().verify_phone_number(
            VerifyPhoneNumberDTO(
                user_id=str(request.user.id),
                code=form.cleaned_data["code"],
            )
        )
        if result.is_success:
            messages.success(
                request, AccountPhoneVerificationApiMessageVO.VERIFIED.value
            )
            return self.profile_redirect(AccountProfileSectionVO.CONTACT)

        form.add_error(
            "code",
            AccountWebProfileErrorPresenter.phone_verification_message_for(
                result.error_code
            ),
        )
        return self.render_panel(
            active_section=AccountProfileSectionVO.CONTACT.value,
            phone_code_form=form,
            status=400,
        )


@method_decorator(
    rate_limit(authenticated_limit=8, anonymous_limit=0, period=300), name="post"
)
class ProfileTicketCreateView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    support_logic_class = BotSupportLogicRepository

    def post(self, request, *args, **kwargs):
        form = SupportTicketTemplateForm(request.POST)
        if not form.is_valid():
            return self.render_panel(
                active_section=AccountProfileSectionVO.TICKETS.value,
                ticket_form=form,
                status=400,
            )
        try:
            self.support_logic_class().create_account_ticket(
                user=request.user,
                subject=form.cleaned_data["subject"],
                message=form.cleaned_data["message"],
            )
        except APIException:
            messages.error(
                request, AccountProfileMessageVO.SUPPORT_OPERATION_FAILED.value
            )
        else:
            messages.success(
                request, AccountProfileMessageVO.SUPPORT_TICKET_CREATED.value
            )
        return self.profile_redirect(AccountProfileSectionVO.TICKETS)


@method_decorator(
    rate_limit(authenticated_limit=15, anonymous_limit=0, period=300), name="post"
)
class ProfileTicketReplyView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    support_logic_class = BotSupportLogicRepository

    def post(self, request, ticket_id, *args, **kwargs):
        form = SupportReplyTemplateForm(request.POST)
        if not form.is_valid():
            messages.error(
                request, AccountProfileMessageVO.SUPPORT_OPERATION_FAILED.value
            )
            return self.profile_redirect(AccountProfileSectionVO.TICKETS)
        try:
            self.support_logic_class().add_account_user_message(
                ticket_id=ticket_id,
                user=request.user,
                message=form.cleaned_data["message"],
            )
        except APIException:
            messages.error(
                request, AccountProfileMessageVO.SUPPORT_OPERATION_FAILED.value
            )
        else:
            messages.success(request, AccountProfileMessageVO.SUPPORT_REPLY_SENT.value)
        return self.profile_redirect(AccountProfileSectionVO.TICKETS)


@method_decorator(
    rate_limit(authenticated_limit=10, anonymous_limit=0, period=300), name="post"
)
class ProfileCourseReviewView(LoginRequiredMixin, ProfilePanelContextMixin, View):
    course_logic_class = CourseLogicRepository

    def post(self, request, course_id, *args, **kwargs):
        form = CourseReviewTemplateForm(request.POST)
        if not form.is_valid():
            messages.error(
                request, AccountProfileMessageVO.REVIEW_OPERATION_FAILED.value
            )
            return self.profile_redirect(AccountProfileSectionVO.COURSES)
        try:
            self.course_logic_class().submit_review(
                user=request.user,
                dto=form.to_dto(course_id=course_id),
            )
        except APIException:
            messages.error(
                request, AccountProfileMessageVO.REVIEW_OPERATION_FAILED.value
            )
        else:
            messages.success(request, AccountProfileMessageVO.REVIEW_SUBMITTED.value)
        return self.profile_redirect(AccountProfileSectionVO.COURSES)


@method_decorator(
    rate_limit(authenticated_limit=8, anonymous_limit=0, period=300), name="post"
)
class ProfilePaymentReceiptUploadView(
    LoginRequiredMixin, ProfilePanelContextMixin, View
):
    billing_logic_class = BillingLogicRepository

    def post(self, request, payment_id, *args, **kwargs):
        form = PaymentReceiptUploadTemplateForm(
            request.POST,
            request.FILES,
            prefix=f"receipt-{payment_id}",
        )
        if not form.is_valid():
            return self.render_panel(
                active_section=AccountProfileSectionVO.BILLING.value,
                receipt_upload_forms={str(payment_id): form},
                status=400,
            )

        try:
            self.billing_logic_class().upload_receipt(
                user=request.user,
                dto=form.to_dto(payment_id=payment_id),
            )
        except APIException:
            form.add_error(
                None,
                AccountProfileMessageVO.PAYMENT_RECEIPT_UPLOAD_FAILED.value,
            )
            return self.render_panel(
                active_section=AccountProfileSectionVO.BILLING.value,
                receipt_upload_forms={str(payment_id): form},
                status=400,
            )

        messages.success(
            request,
            AccountProfileMessageVO.PAYMENT_RECEIPT_UPLOADED.value,
        )
        return self.profile_redirect(AccountProfileSectionVO.BILLING)
