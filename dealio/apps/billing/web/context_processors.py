from dealio.apps.billing.repositories.adapters.basket_postgres_adapter import (
    BasketPostgresAdapter,
)


def basket_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"basket_item_count": 0}
    return {"basket_item_count": BasketPostgresAdapter().count_items(request.user)}
