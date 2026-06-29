from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from dealio.apps.billing.dtos import CheckoutDTO, PaymentConfirmDTO, PaymentStartDTO
from dealio.apps.billing.repositories.logic import BillingLogicRepository
from dealio.apps.billing.serializers import (
    CheckoutSerializer,
    OrderSerializer,
    PaymentConfirmSerializer,
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

    def get(self, request):
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
