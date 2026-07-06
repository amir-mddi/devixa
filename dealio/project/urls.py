import os

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as django_static_serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.shared.views import prometheus_metrics
from dealio.apps.telegram_bot.views import BaleWebhookAPIView, RubikaWebhookAPIView


class PrivateSwaggerView(SpectacularSwaggerView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


class PrivateRedocView(SpectacularRedocView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


PREFIX_URL = "api/v1/"
urlpatterns = [
                  path("", include("dealio.apps.accounts.web.urls")),
                  path("", include("dealio.apps.pages.web.urls")),
                  path("", include("dealio.apps.courses.web.urls")),
                  path(PREFIX_URL + "account/", include("dealio.apps.accounts.urls")),
                  path(PREFIX_URL + "courses/", include("dealio.apps.courses.urls")),
                  path(PREFIX_URL + "billing/", include("dealio.apps.billing.urls")),
                  path("api/shared/", include("dealio.apps.shared.urls")),
                  path("api/telegram/", include("dealio.apps.telegram_bot.urls")),
                  path("api/bale/webhook/", BaleWebhookAPIView.as_view(), name="bale-webhook"),
                  path("api/rubika/webhook/", RubikaWebhookAPIView.as_view(), name="rubika-webhook"),
                  # path('', include('django_prometheus.urls')),
                  path("metrics/", prometheus_metrics, name="prometheus-metrics"),
                  path(os.environ.get("ADMIN_PANEL_URL", "admin/"), admin.site.urls),
              ] + debug_toolbar_urls()

static_document_root = CommonUtils.get_first_staticfiles_dir()

if CommonUtils.should_serve_static_files() and static_document_root:
    urlpatterns += [
        re_path(
            r"^static/(?P<path>.*)$",
            django_static_serve,
            {"document_root": static_document_root},
        )
    ]

if settings.DEBUG:
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