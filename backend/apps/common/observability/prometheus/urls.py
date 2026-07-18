from django.urls import path

from .views import prometheus_metrics

app_name = "prometheus_observability"

urlpatterns = [
    # Register both forms so CommonMiddleware cannot disclose the endpoint with
    # an unauthenticated APPEND_SLASH redirect.
    path("metrics", prometheus_metrics, name="metrics-no-slash"),
    path("metrics/", prometheus_metrics, name="metrics"),
]
