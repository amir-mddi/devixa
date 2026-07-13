from django.urls import path

from dealio.apps.billing.vo import BasketWebPathVO, BasketWebRouteNameVO
from dealio.apps.billing.web.views import (
    BasketAddItemView,
    BasketApplyDiscountView,
    BasketClearView,
    BasketPageView,
    BasketPaymentStartView,
    BasketRemoveDiscountView,
    BasketRemoveItemView,
    CardToCardPaymentView,
    CardToCardReceiptUploadView,
    CheckoutPageView,
)

app_name = "billing_web"

urlpatterns = [
    path(BasketWebPathVO.BASKET.value, BasketPageView.as_view(), name=BasketWebRouteNameVO.BASKET.value),
    path(BasketWebPathVO.ADD_ITEM.value, BasketAddItemView.as_view(), name=BasketWebRouteNameVO.ADD_ITEM.value),
    path(BasketWebPathVO.REMOVE_ITEM.value, BasketRemoveItemView.as_view(), name=BasketWebRouteNameVO.REMOVE_ITEM.value),
    path(BasketWebPathVO.CLEAR.value, BasketClearView.as_view(), name=BasketWebRouteNameVO.CLEAR.value),
    path(BasketWebPathVO.APPLY_DISCOUNT.value, BasketApplyDiscountView.as_view(), name=BasketWebRouteNameVO.APPLY_DISCOUNT.value),
    path(BasketWebPathVO.REMOVE_DISCOUNT.value, BasketRemoveDiscountView.as_view(), name=BasketWebRouteNameVO.REMOVE_DISCOUNT.value),
    path(BasketWebPathVO.CHECKOUT.value, CheckoutPageView.as_view(), name=BasketWebRouteNameVO.CHECKOUT.value),
    path(BasketWebPathVO.START_PAYMENT.value, BasketPaymentStartView.as_view(), name=BasketWebRouteNameVO.START_PAYMENT.value),
    path(BasketWebPathVO.PAYMENT_DETAIL.value, CardToCardPaymentView.as_view(), name=BasketWebRouteNameVO.PAYMENT_DETAIL.value),
    path(BasketWebPathVO.UPLOAD_RECEIPT.value, CardToCardReceiptUploadView.as_view(), name=BasketWebRouteNameVO.UPLOAD_RECEIPT.value),
]
