from django.urls import path

from .views import liveness, readiness

app_name = "health_observability"

urlpatterns = [
    path("health/live/", liveness, name="liveness"),
    path("health/ready/", readiness, name="readiness"),
]
