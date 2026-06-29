from django.urls import path

from dealio.apps.billing.views import (
    AdminOrdersAPIView,
    AdminPaymentsAPIView,
    CheckoutAPIView,
    MyOrdersAPIView,
    MyPaymentsAPIView,
    PaymentConfirmAPIView,
    PaymentStartAPIView,
)

urlpatterns = [
    path("checkout/", CheckoutAPIView.as_view(), name="billing-checkout"),
    path("orders/", MyOrdersAPIView.as_view(), name="my-orders"),
    path("orders/<uuid:order_id>/", MyOrdersAPIView.as_view(), name="my-order-detail"),
    path("payments/", MyPaymentsAPIView.as_view(), name="my-payments"),
    path("payments/start/", PaymentStartAPIView.as_view(), name="payment-start"),
    path("payments/confirm/", PaymentConfirmAPIView.as_view(), name="payment-confirm"),
    path("admin/orders/", AdminOrdersAPIView.as_view(), name="admin-orders"),
    path("admin/payments/", AdminPaymentsAPIView.as_view(), name="admin-payments"),
]
