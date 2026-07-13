from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import APIException

from dealio.apps.billing.dtos import (
    BasketAddItemDTO,
    BasketApplyDiscountDTO,
    BasketCheckoutDTO,
    BasketRemoveItemDTO,
    PaymentStartDTO,
)
from dealio.apps.billing.enums import PaymentProviderEnum, PaymentStatusEnum
from dealio.apps.billing.logic import BasketLogic
from dealio.apps.billing.repositories.logic import BillingLogicRepository
from dealio.apps.billing.vo import (
    BasketWebFieldVO,
    BasketWebMessageVO,
    BasketWebReverseNameVO,
    BasketWebTemplateVO,
)
from dealio.apps.billing.web.forms import (
    BasketDiscountForm,
    BasketPaymentMethodForm,
    PaymentReceiptUploadTemplateForm,
)


class BasketWebErrorPresenter:
    TRANSLATIONS = {
        "Discount code is invalid.": "کد تخفیف معتبر نیست.",
        "Discount code is not active yet.": "زمان استفاده از این کد تخفیف هنوز شروع نشده است.",
        "Discount code is expired.": "کد تخفیف منقضی شده است.",
        "Discount usage limit has been reached.": "ظرفیت استفاده از این کد تخفیف تکمیل شده است.",
        "Order amount is lower than this discount minimum amount.": "مبلغ سبد برای استفاده از این کد تخفیف کافی نیست.",
        "Discount code is not valid for the courses in this order.": "این کد تخفیف برای دوره‌های سبد شما قابل استفاده نیست.",
        "You have already used this discount code.": "شما قبلاً از این کد تخفیف استفاده کرده‌اید.",
        "Order has no items.": BasketWebMessageVO.EMPTY.value,
    }

    @classmethod
    def from_exception(cls, exc: Exception) -> str:
        detail = getattr(exc, "detail", None)
        if isinstance(detail, dict):
            value = next(iter(detail.values()), BasketWebMessageVO.INVALID_ACTION.value)
            if isinstance(value, (list, tuple)):
                value = value[0] if value else BasketWebMessageVO.INVALID_ACTION.value
        elif isinstance(detail, (list, tuple)):
            value = detail[0] if detail else BasketWebMessageVO.INVALID_ACTION.value
        else:
            value = detail or str(exc)
        text = str(value)
        return cls.TRANSLATIONS.get(text, text or BasketWebMessageVO.INVALID_ACTION.value)


class SafeBasketRedirectMixin:
    def redirect_target(self):
        candidate = self.request.POST.get("next", "")
        if candidate and url_has_allowed_host_and_scheme(
            candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return reverse(BasketWebReverseNameVO.BASKET.value)


class BasketContextMixin:
    basket_logic_class = BasketLogic

    def basket_context(self, *, discount_form=None, **extra):
        context = {
            "basket": self.basket_logic_class().get_summary(self.request.user),
            "discount_form": discount_form or BasketDiscountForm(),
        }
        context.update(extra)
        return context


class BasketPageView(LoginRequiredMixin, BasketContextMixin, TemplateView):
    template_name = BasketWebTemplateVO.BASKET.value

    def get_context_data(self, **kwargs):
        return self.basket_context()


class BasketAddItemView(LoginRequiredMixin, SafeBasketRedirectMixin, View):
    basket_logic_class = BasketLogic

    def post(self, request, *args, **kwargs):
        try:
            _, created = self.basket_logic_class().add_item(
                request.user,
                BasketAddItemDTO(
                    course_id=request.POST.get(BasketWebFieldVO.COURSE_ID.value)
                ),
            )
        except (APIException, PydanticValidationError) as exc:
            messages.error(request, BasketWebErrorPresenter.from_exception(exc))
        else:
            messages.success(
                request,
                BasketWebMessageVO.ITEM_ADDED.value
                if created
                else BasketWebMessageVO.ITEM_ALREADY_EXISTS.value,
            )
        return redirect(self.redirect_target())


class BasketRemoveItemView(LoginRequiredMixin, View):
    basket_logic_class = BasketLogic

    def post(self, request, item_id, *args, **kwargs):
        try:
            self.basket_logic_class().remove_item(
                request.user,
                BasketRemoveItemDTO(item_id=item_id),
            )
        except APIException as exc:
            messages.error(request, BasketWebErrorPresenter.from_exception(exc))
        else:
            messages.success(request, BasketWebMessageVO.ITEM_REMOVED.value)
        return redirect(BasketWebReverseNameVO.BASKET.value)


class BasketClearView(LoginRequiredMixin, View):
    basket_logic_class = BasketLogic

    def post(self, request, *args, **kwargs):
        try:
            self.basket_logic_class().clear(request.user)
        except APIException as exc:
            messages.error(request, BasketWebErrorPresenter.from_exception(exc))
        else:
            messages.success(request, BasketWebMessageVO.CLEARED.value)
        return redirect(BasketWebReverseNameVO.BASKET.value)


class BasketApplyDiscountView(LoginRequiredMixin, BasketContextMixin, View):
    template_name = BasketWebTemplateVO.BASKET.value

    def post(self, request, *args, **kwargs):
        form = BasketDiscountForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                self.basket_context(discount_form=form),
                status=400,
            )
        try:
            self.basket_logic_class().apply_discount(
                request.user,
                BasketApplyDiscountDTO(code=form.cleaned_data[BasketWebFieldVO.CODE.value]),
            )
        except APIException as exc:
            form.add_error(None, BasketWebErrorPresenter.from_exception(exc))
            return render(
                request,
                self.template_name,
                self.basket_context(discount_form=form),
                status=400,
            )
        messages.success(request, BasketWebMessageVO.DISCOUNT_APPLIED.value)
        return redirect(BasketWebReverseNameVO.BASKET.value)


class BasketRemoveDiscountView(LoginRequiredMixin, View):
    basket_logic_class = BasketLogic

    def post(self, request, *args, **kwargs):
        try:
            self.basket_logic_class().remove_discount(request.user)
        except APIException as exc:
            messages.error(request, BasketWebErrorPresenter.from_exception(exc))
        else:
            messages.success(request, BasketWebMessageVO.DISCOUNT_REMOVED.value)
        return redirect(BasketWebReverseNameVO.BASKET.value)


class CheckoutPageView(LoginRequiredMixin, TemplateView):
    template_name = BasketWebTemplateVO.CHECKOUT.value
    basket_logic_class = BasketLogic

    def get(self, request, *args, **kwargs):
        try:
            basket = self.basket_logic_class().get_checkout_summary(request.user)
        except APIException as exc:
            messages.error(request, BasketWebErrorPresenter.from_exception(exc))
            return redirect(BasketWebReverseNameVO.BASKET.value)
        return render(
            request,
            self.template_name,
            {
                "basket": basket,
                "payment_form": BasketPaymentMethodForm(),
            },
        )


class BasketPaymentStartView(LoginRequiredMixin, View):
    basket_logic_class = BasketLogic
    billing_logic_class = BillingLogicRepository

    def post(self, request, *args, **kwargs):
        form = BasketPaymentMethodForm(request.POST)
        if not form.is_valid():
            messages.error(request, BasketWebMessageVO.INVALID_ACTION.value)
            return redirect(BasketWebReverseNameVO.CHECKOUT.value)
        try:
            summary, completed = self.basket_logic_class().prepare_checkout(
                request.user,
                BasketCheckoutDTO(order_id=request.POST.get("order_id")),
            )
            if completed:
                messages.success(request, BasketWebMessageVO.FREE_ORDER_COMPLETED.value)
                return redirect(f"{reverse('accounts_web:profile')}#courses")
            payment = self.billing_logic_class().start_payment(
                request.user,
                PaymentStartDTO(
                    order_id=summary.order.id,
                    provider=PaymentProviderEnum.CARD_TO_CARD,
                ),
            )
        except (APIException, PydanticValidationError) as exc:
            messages.error(request, BasketWebErrorPresenter.from_exception(exc))
            return redirect(BasketWebReverseNameVO.CHECKOUT.value)
        messages.success(request, BasketWebMessageVO.PAYMENT_CREATED.value)
        return redirect(BasketWebReverseNameVO.PAYMENT_DETAIL.value, payment_id=payment.id)


class CardToCardPaymentView(LoginRequiredMixin, View):
    template_name = BasketWebTemplateVO.CARD_TO_CARD.value
    billing_logic_class = BillingLogicRepository

    def get(self, request, payment_id, *args, **kwargs):
        try:
            payment = self.billing_logic_class().get_payment_for_user(payment_id, request.user)
        except APIException as exc:
            raise Http404(BasketWebMessageVO.INVALID_ACTION.value) from exc
        if payment.user_id != request.user.id:
            raise Http404(BasketWebMessageVO.INVALID_ACTION.value)
        return self.render_payment(request, payment)

    def render_payment(self, request, payment, *, receipt_form=None, status=200):
        if payment.provider not in {
            PaymentProviderEnum.CARD_TO_CARD.value,
            PaymentProviderEnum.MANUAL.value,
        }:
            messages.error(request, BasketWebMessageVO.INVALID_ACTION.value)
            return redirect(BasketWebReverseNameVO.BASKET.value)
        return render(
            request,
            self.template_name,
            {
                "payment": payment,
                "order_items": payment.order.items.filter(is_deleted=False).select_related("course"),
                "bank_info": payment.response_payload or {},
                "bank_info_configured": any(
                    str((payment.response_payload or {}).get(key, "") or "").strip()
                    for key in ("card_number", "account_number", "iban")
                ),
                "can_upload_receipt": self.billing_logic_class().can_upload_receipt(payment),
                "receipt_form": receipt_form
                or PaymentReceiptUploadTemplateForm(
                    initial={BasketWebFieldVO.PAID_AMOUNT.value: payment.amount}
                ),
                "payment_succeeded": payment.status == PaymentStatusEnum.SUCCEEDED.value,
                "payment_pending": payment.status == PaymentStatusEnum.PENDING_VERIFICATION.value,
                "receipts": tuple(payment.receipts.filter(is_deleted=False).order_by("-created_at")),
            },
            status=status,
        )


class CardToCardReceiptUploadView(CardToCardPaymentView):
    def post(self, request, payment_id, *args, **kwargs):
        try:
            payment = self.billing_logic_class().get_payment_for_user(payment_id, request.user)
        except APIException as exc:
            raise Http404(BasketWebMessageVO.INVALID_ACTION.value) from exc
        if payment.user_id != request.user.id:
            raise Http404(BasketWebMessageVO.INVALID_ACTION.value)
        form = PaymentReceiptUploadTemplateForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_payment(request, payment, receipt_form=form, status=400)
        try:
            self.billing_logic_class().upload_receipt(
                request.user,
                form.to_dto(payment_id=payment.id),
            )
        except APIException as exc:
            form.add_error(None, BasketWebErrorPresenter.from_exception(exc))
            payment.refresh_from_db()
            return self.render_payment(request, payment, receipt_form=form, status=400)
        messages.success(request, BasketWebMessageVO.RECEIPT_UPLOADED.value)
        return redirect(BasketWebReverseNameVO.PAYMENT_DETAIL.value, payment_id=payment.id)
