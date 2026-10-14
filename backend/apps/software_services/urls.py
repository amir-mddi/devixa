from django.urls import path
from backend.apps.software_services.value_objects.request_vo import SoftwareRequestRouteVO
from backend.apps.software_services.views import SoftwareServicePageView

app_name = SoftwareRequestRouteVO.NAMESPACE.value
urlpatterns = [path(SoftwareRequestRouteVO.PATH.value, SoftwareServicePageView.as_view(), name=SoftwareRequestRouteVO.LANDING.value)]
