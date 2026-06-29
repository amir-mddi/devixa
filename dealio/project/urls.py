import os

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from dealio.apps.shared.views import prometheus_metrics
from dealio.project import settings


class PrivateSwaggerView(SpectacularSwaggerView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


class PrivateRedocView(SpectacularRedocView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


PREFIX_URL = "api/v1/"
urlpatterns = [
                  path(PREFIX_URL + "account/", include("dealio.apps.accounts.urls")),
                  path(PREFIX_URL + "courses/", include("dealio.apps.courses.urls")),
                  path(PREFIX_URL + "billing/", include("dealio.apps.billing.urls")),
                  path("api/shared/", include("dealio.apps.shared.urls")),
                  path("api/telegram/", include("dealio.apps.telegram_bot.urls")),
                  # path('', include('django_prometheus.urls')),
                  path("metrics/", prometheus_metrics, name="prometheus-metrics"),
                  path(os.environ.get("ADMIN_PANEL_URL", "admin/"), admin.site.urls),
              ] + debug_toolbar_urls()

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/swagger-ui/",
        PrivateSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        PrivateRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]