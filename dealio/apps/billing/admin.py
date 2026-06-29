from django.contrib import admin

from dealio.apps.billing.models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("course_title", "unit_price", "quantity", "total_price")


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
