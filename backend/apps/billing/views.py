from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from asgiref.sync import sync_to_async
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from backend.apps.billing.dtos import (
    CheckoutDTO,
    PaymentConfirmDTO,
    PaymentGatewayCallbackDTO,
    PaymentReceiptReviewDTO,
    PaymentReceiptUploadDTO,
    PaymentStartDTO,
)
from backend.apps.billing.enums import PaymentProviderEnum, PaymentReceiptSourceEnum
from backend.apps.billing.repositories.logic import BillingLogicRepository
from backend.apps.billing.serializers import (
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
from backend.apps.billing.vo import BillingMessagesVO
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.async_api import AsyncAPIView as APIView
from backend.apps.common.utils.async_drf import serializer_data, validate_serializer
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    validate_public_https_url,
)
from backend.apps.common.utils.pagination_response_mixin import PaginatedResponseMixin
from backend.apps.core_models.constants.common_vo import ResponseVO
from backend.apps.shared.throttling import PaymentCallbackThrottle

logger = CommonUtils.get_project_logger(__name__)


async def _serialize(serializer_class, instance, *, request):
    return await serializer_data(
        serializer_class(instance, context={"request": request})
    )


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        order, created = await self.logic.create_checkout_order_async(
            user=request.user,
            dto=CheckoutDTO(**serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "created": created,
                "requires_payment": order.total_amount > 0 and order.status != "paid",
                "order": await _serialize(OrderSerializer, order, request=request),
            },
            status_code=ResponseVO.http_201 if created else ResponseVO.http_200,
        )


class MyOrdersAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def get(self, request, order_id=None):
        if order_id:
            order = await self.logic.get_order_for_user_async(
                order_id=order_id,
                user=request.user,
            )
            return ResponseUtil(
                data=await _serialize(OrderSerializer, order, request=request)
            )
        queryset = await self.logic.list_user_orders_async(request.user)
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, OrderSerializer)


class MyPaymentsAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def get(self, request, payment_id=None):
        if payment_id:
            payment = await self.logic.get_payment_for_user_async(
                payment_id=payment_id,
                user=request.user,
            )
            return ResponseUtil(
                data=await _serialize(PaymentSerializer, payment, request=request)
            )
        queryset = await self.logic.list_user_payments_async(request.user)
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, PaymentSerializer)


class PaymentStartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentStartSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        payment = await self.logic.start_payment_async(
            user=request.user,
            dto=PaymentStartDTO(**serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.PAYMENT_CREATED,
                "payment": await _serialize(
                    PaymentSerializer,
                    payment,
                    request=request,
                ),
            },
            status_code=ResponseVO.http_201,
        )


class PaymentConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentConfirmSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        payment = await self.logic.confirm_payment_async(
            actor=request.user,
            dto=PaymentConfirmDTO(**serializer.validated_data),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.PAYMENT_CONFIRMED,
                "payment": await _serialize(
                    PaymentSerializer,
                    payment,
                    request=request,
                ),
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

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        receipt = await self.logic.upload_receipt_async(
            user=request.user,
            dto=PaymentReceiptUploadDTO(
                **serializer.validated_data,
                source=PaymentReceiptSourceEnum.WEB,
            ),
        )
        return ResponseUtil(
            data={
                "detail": BillingMessagesVO.RECEIPT_CREATED,
                "receipt": await _serialize(
                    PaymentReceiptSerializer,
                    receipt,
                    request=request,
                ),
            },
            status_code=ResponseVO.http_201,
        )


class PaymentGatewayCallbackAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PaymentCallbackThrottle]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def get(
        self,
        request,
        provider: str = PaymentProviderEnum.PARDAKHTYAR.value,
    ):
        return await self._handle(request, provider)

    async def post(
        self,
        request,
        provider: str = PaymentProviderEnum.PARDAKHTYAR.value,
    ):
        return await self._handle(request, provider)

    async def _handle(self, request, provider: str):
        payload = request.query_params.dict()
        if isinstance(request.data, dict):
            payload.update(request.data)
        try:
            payment, verification_result = (
                await self.logic.confirm_gateway_callback_async(
                    PaymentGatewayCallbackDTO(provider=provider, payload=payload)
                )
            )
        except (NotFound, ValidationError):
            return ResponseUtil(
                data={"detail": "Invalid payment callback."},
                status_code=ResponseVO.http_400,
            )

        success = bool(verification_result.get("is_success"))
        redirect_url = self._redirect_url(success=success, payment=payment)
        if redirect_url:
            response = redirect(redirect_url)
            response["Cache-Control"] = "no-store"
            return response

        response = ResponseUtil(
            data={
                "detail": BillingMessagesVO.GATEWAY_VERIFIED,
                "is_success": success,
            },
            status_code=ResponseVO.http_200,
        )
        response["Cache-Control"] = "no-store"
        return response

    @staticmethod
    def _redirect_url(success: bool, payment) -> str:
        configured_url = (
            getattr(settings, "PARDAKHTYAR_FRONTEND_SUCCESS_URL", "")
            if success
            else getattr(settings, "PARDAKHTYAR_FRONTEND_FAILED_URL", "")
        )
        configured_url = str(configured_url or "").strip()
        if not configured_url:
            return ""
        allowed_hosts = (
            getattr(settings, "PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS", ()) or ()
        )
        try:
            safe_url = validate_public_https_url(
                configured_url,
                allowed_hosts=allowed_hosts,
                resolve_dns=False,
            )
        except UnsafeOutboundUrlError:
            logger.error("Configured payment frontend redirect URL is unsafe.")
            return ""
        parsed = urlsplit(safe_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.update(
            {
                "payment_id": str(payment.id),
                "order_number": payment.order.order_number,
                "status": payment.status,
            }
        )
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), "")
        )


class _AdminPaginatedBillingAPIView(PaginatedResponseMixin, APIView):
    permission_classes = [IsAdminUser]
    serializer_class = None
    logic_method_name = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def get(self, request):
        queryset = await getattr(self.logic, self.logic_method_name)(
            status=request.query_params.get("status")
        )
        return await sync_to_async(
            self.paginated_response,
            thread_sensitive=True,
        )(request, queryset, self.serializer_class)


class AdminOrdersAPIView(_AdminPaginatedBillingAPIView):
    serializer_class = OrderSerializer
    logic_method_name = "list_orders_for_admin_async"


class AdminPaymentsAPIView(_AdminPaginatedBillingAPIView):
    serializer_class = PaymentSerializer
    logic_method_name = "list_payments_for_admin_async"


class AdminPaymentReceiptsAPIView(_AdminPaginatedBillingAPIView):
    serializer_class = AdminPaymentReceiptSerializer
    logic_method_name = "list_receipts_for_admin_async"


class AdminPaymentReceiptReviewAPIView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = PaymentReceiptReviewSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = BillingLogicRepository()

    async def post(self, request, receipt_id):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        receipt, payment = await self.logic.review_receipt_async(
            actor=request.user,
            dto=PaymentReceiptReviewDTO(
                receipt_id=receipt_id,
                **serializer.validated_data,
            ),
        )
        return ResponseUtil(
            data={
                "detail": (
                    BillingMessagesVO.RECEIPT_APPROVED
                    if serializer.validated_data["approve"]
                    else BillingMessagesVO.RECEIPT_REJECTED
                ),
                "receipt": await _serialize(
                    AdminPaymentReceiptSerializer,
                    receipt,
                    request=request,
                ),
                "payment": await _serialize(
                    PaymentSerializer,
                    payment,
                    request=request,
                ),
            },
            status_code=ResponseVO.http_200,
        )
