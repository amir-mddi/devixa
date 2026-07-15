from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from backend.apps.shared.views import ApiKeyManagementViewSet, ProjectConfigAPIView

router = routers.DefaultRouter()
# router.register(r'celery-healthy', ManageMetricsViewSet, basename='register')
router.register(r"api-key-management", ApiKeyManagementViewSet, basename="api-key-management")

urlpatterns = [
    path("", include(router.urls)),
    path("project-config/", ProjectConfigAPIView.as_view(), name="project-config"),
]
