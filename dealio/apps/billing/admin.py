from django.contrib import admin, messages

from dealio.apps.billing.dtos import PaymentReceiptReviewDTO
from dealio.apps.billing.enums import PaymentReceiptStatusEnum
from dealio.apps.billing.models import DiscountCode, DiscountRedemption, Order, OrderItem, Payment, PaymentReceipt
from dealio.apps.billing.repositories.logic import BillingLogicRepository


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("course_title", "unit_price", "quantity", "total_price")


class PaymentReceiptInline(admin.TabularInline):
    model = PaymentReceipt
    extra = 0
    readonly_fields = (
        "status",
        "source",
        "receipt_file",
        "receipt_file_url",
        "tracking_code",
        "paid_amount",
        "reviewed_by",
        "reviewed_at",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "total_amount", "currency", "paid_at", "created_at")
    list_filter = ("status", "currency", "created_at", "paid_at")
    search_fields = ("order_number", "user__username", "user__email")
    readonly_fields = ("order_number", "paid_at")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "course_title", "unit_price", "quantity", "total_price")
    search_fields = ("order__order_number", "course_title", "course__title")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_number", "order", "user", "provider", "status", "amount", "currency", "paid_at", "created_at")
    list_filter = ("provider", "status", "currency", "created_at", "paid_at")
    search_fields = ("payment_number", "order__order_number", "transaction_id", "authority", "user__username")
    readonly_fields = ("payment_number", "paid_at", "verified_at")
    inlines = [PaymentReceiptInline]


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "user",
        "status",
        "source",
        "tracking_code",
        "paid_amount",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_filter = ("status", "source", "created_at", "reviewed_at")
    search_fields = ("payment__payment_number", "payment__order__order_number", "tracking_code", "user__username", "user__email")
    readonly_fields = ("reviewed_at",)
    actions = ["approve_selected_receipts", "reject_selected_receipts"]

    @admin.action(description="Approve selected payment receipts and activate enrollments")
    def approve_selected_receipts(self, request, queryset):
        logic = BillingLogicRepository()
        approved_count = 0
        for receipt in queryset.filter(status=PaymentReceiptStatusEnum.PENDING.value, is_deleted=False):
            logic.review_receipt(
                actor=request.user,
                dto=PaymentReceiptReviewDTO(
                    receipt_id=receipt.id,
                    approve=True,
                    transaction_id=receipt.tracking_code,
                    admin_note="Approved from Django admin.",
                ),
            )
            approved_count += 1
        self.message_user(request, f"{approved_count} receipt(s) approved.", level=messages.SUCCESS)

    @admin.action(description="Reject selected payment receipts")
    def reject_selected_receipts(self, request, queryset):
        logic = BillingLogicRepository()
        rejected_count = 0
        for receipt in queryset.filter(status=PaymentReceiptStatusEnum.PENDING.value, is_deleted=False):
            logic.review_receipt(
                actor=request.user,
                dto=PaymentReceiptReviewDTO(
                    receipt_id=receipt.id,
                    approve=False,
                    admin_note="Rejected from Django admin.",
                ),
            )
            rejected_count += 1
        self.message_user(request, f"{rejected_count} receipt(s) rejected.", level=messages.WARNING)


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "discount_type", "value", "usage_limit", "used_count", "is_active", "created_at")
    list_filter = ("discount_type", "is_active", "is_deleted", "created_at")
    search_fields = ("code", "title")
    filter_horizontal = ("courses",)


@admin.register(DiscountRedemption)
class DiscountRedemptionAdmin(admin.ModelAdmin):
    list_display = ("code", "discount", "order", "user", "amount", "created_at")
    list_filter = ("code", "created_at")
    search_fields = ("code", "order__order_number", "user__email", "user__username")
