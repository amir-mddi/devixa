from django.conf import settings
from django.shortcuts import redirect
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from dealio.apps.billing.dtos import (
    CheckoutDTO,
    PaymentConfirmDTO,
    PaymentGatewayCallbackDTO,
    PaymentReceiptReviewDTO,
    PaymentReceiptUploadDTO,
    PaymentStartDTO,
)
from dealio.apps.billing.enums import PaymentProviderEnum, PaymentReceiptSourceEnum
from dealio.apps.billing.repositories.logic import BillingLogicRepository
from dealio.apps.billing.serializers import (
    AdminPaymentReceiptSerializer,
    CheckoutSerializer,
    OrderSerializer,
    PaymentConfirmSerializer,
    PaymentReceiptReviewSerializer,
    PaymentReceiptSerializer,
    PaymentReceiptUploadSerializer,
    PaymentSerializer,
    PaymentStartSerializer,
)
from dealio.apps.billing.vo import BillingMessagesVO
from dealio.apps.common.response_utils import ResponseUtil
from dealio.apps.common.utils.pagination_response_mixin import PaginatedResponseMixin
from dealio.apps.core_models.constants.common_vo import ResponseVO


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, created = self.logic.create_checkout_order(
            user=request.user,
            dto=CheckoutDTO(**serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "created": created,
                "requires_payment": order.total_amount > 0 and order.status != "paid",
                "order": OrderSerializer(order, context={"request": request}).data,
            },
            status_code=ResponseVO.http_201 if created else ResponseVO.http_200,
        )


class MyOrdersAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def get(self, request, order_id=None):
        if order_id:
            order = self.logic.get_order_for_user(order_id=order_id, user=request.user)
            return ResponseUtil(data=OrderSerializer(order, context={"request": request}).data)
        queryset = self.logic.list_user_orders(request.user)
        return self.paginated_response(request, queryset, OrderSerializer)


class MyPaymentsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def get(self, request, payment_id=None):
        if payment_id:
            payment = self.logic.get_payment_for_user(payment_id=payment_id, user=request.user)
            return ResponseUtil(data=PaymentSerializer(payment, context={"request": request}).data)
        queryset = self.logic.list_user_payments(request.user)
        return self.paginated_response(request, queryset, PaymentSerializer)


class PaymentStartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentStartSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def post(self, request):
        serializer = PaymentStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = self.logic.start_payment(
            user=request.user,
            dto=PaymentStartDTO(**serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.PAYMENT_CREATED,
                "payment": PaymentSerializer(payment, context={"request": request}).data,
            },
            status_code=ResponseVO.http_201,
        )


class PaymentConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentConfirmSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def post(self, request):
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = self.logic.confirm_payment(
            actor=request.user,
            dto=PaymentConfirmDTO(**serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.PAYMENT_CONFIRMED,
                "payment": PaymentSerializer(payment, context={"request": request}).data,
            },
            status_code=ResponseVO.http_200,
        )


class PaymentReceiptUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = PaymentReceiptUploadSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def post(self, request):
        serializer = PaymentReceiptUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = self.logic.upload_receipt(
            user=request.user,
            dto=PaymentReceiptUploadDTO(
                **serializer.validated_data,
                source=PaymentReceiptSourceEnum.WEB,
            ),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.RECEIPT_CREATED,
                "receipt": PaymentReceiptSerializer(receipt, context={"request": request}).data,
            },
            status_code=ResponseVO.http_201,
        )


class PaymentGatewayCallbackAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def get(self, request, provider: str = PaymentProviderEnum.PARDAKHTYAR.value):
        return self._handle(request, provider)

    def post(self, request, provider: str = PaymentProviderEnum.PARDAKHTYAR.value):
        return self._handle(request, provider)

    def _handle(self, request, provider: str):
        payload = request.query_params.dict()
        payload.update(request.data if isinstance(request.data, dict) else {})
        payment, verification_result = self.logic.confirm_gateway_callback(
            PaymentGatewayCallbackDTO(provider=provider, payload=payload)
        )
        success = bool(verification_result.get("is_success"))
        redirect_url = self._redirect_url(success=success, payment=payment)
        if redirect_url:
            return redirect(redirect_url)
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.GATEWAY_VERIFIED,
                "is_success": success,
                "payment": PaymentSerializer(payment, context={"request": request}).data,
            },
            status_code=ResponseVO.http_200,
        )

    @staticmethod
    def _redirect_url(success: bool, payment) -> str:
        url = getattr(settings, "PARDAKHTYAR_FRONTEND_SUCCESS_URL", "") if success else getattr(settings, "PARDAKHTYAR_FRONTEND_FAILED_URL", "")
        if not url:
            return ""
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}payment_id={payment.id}&order_number={payment.order.order_number}&status={payment.status}"


class AdminOrdersAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def get(self, request):
        queryset = self.logic.list_orders_for_admin(status=request.query_params.get("status"))
        return self.paginated_response(request, queryset, OrderSerializer)


class AdminPaymentsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def get(self, request):
        queryset = self.logic.list_payments_for_admin(status=request.query_params.get("status"))
        return self.paginated_response(request, queryset, PaymentSerializer)


class AdminPaymentReceiptsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def get(self, request):
        queryset = self.logic.list_receipts_for_admin(status=request.query_params.get("status"))
        return self.paginated_response(request, queryset, AdminPaymentReceiptSerializer)


class AdminPaymentReceiptReviewAPIView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = PaymentReceiptReviewSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    def post(self, request, receipt_id):
        serializer = PaymentReceiptReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt, payment = self.logic.review_receipt(
            actor=request.user,
            dto=PaymentReceiptReviewDTO(receipt_id=receipt_id, **serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.RECEIPT_APPROVED if serializer.validated_data["approve"] else BillingMessagesVO.RECEIPT_REJECTED,
                "receipt": AdminPaymentReceiptSerializer(receipt, context={"request": request}).data,
                "payment": PaymentSerializer(payment, context={"request": request}).data,
            },
            status_code=ResponseVO.http_200,
        )
