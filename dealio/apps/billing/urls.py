from django.urls import path

from dealio.apps.billing.views import (
    AdminOrdersAPIView,
    AdminPaymentReceiptReviewAPIView,
    AdminPaymentReceiptsAPIView,
    AdminPaymentsAPIView,
    CheckoutAPIView,
    MyOrdersAPIView,
    MyPaymentsAPIView,
    PaymentConfirmAPIView,
    PaymentGatewayCallbackAPIView,
    PaymentReceiptUploadAPIView,
    PaymentStartAPIView,
)

urlpatterns = [
    path("checkout/", CheckoutAPIView.as_view(), name="billing-checkout"),
    path("orders/", MyOrdersAPIView.as_view(), name="my-orders"),
    path("orders/<uuid:order_id>/", MyOrdersAPIView.as_view(), name="my-order-detail"),
    path("payments/", MyPaymentsAPIView.as_view(), name="my-payments"),
    path("payments/<uuid:payment_id>/", MyPaymentsAPIView.as_view(), name="my-payment-detail"),
    path("payments/start/", PaymentStartAPIView.as_view(), name="payment-start"),
    path("payments/confirm/", PaymentConfirmAPIView.as_view(), name="payment-confirm"),
    path("payments/receipts/upload/", PaymentReceiptUploadAPIView.as_view(), name="payment-receipt-upload"),
    path("payments/pardakhtyar/callback/", PaymentGatewayCallbackAPIView.as_view(), name="pardakhtyar-payment-callback"),
    path("payments/<str:provider>/callback/", PaymentGatewayCallbackAPIView.as_view(), name="payment-provider-callback"),
    path("admin/orders/", AdminOrdersAPIView.as_view(), name="admin-orders"),
    path("admin/payments/", AdminPaymentsAPIView.as_view(), name="admin-payments"),
    path("admin/payment-receipts/", AdminPaymentReceiptsAPIView.as_view(), name="admin-payment-receipts"),
    path("admin/payment-receipts/<uuid:receipt_id>/review/", AdminPaymentReceiptReviewAPIView.as_view(), name="admin-payment-receipt-review"),
]
