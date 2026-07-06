from __future__ import annotations

from django.urls import path

from dealio.apps.courses.vo.roadmap_vo import (
    CourseWebAppNameVO,
    CourseWebPathVO,
    CourseWebRouteNameVO,
)
from dealio.apps.courses.web.views import (
    CourseDetailPageView,
    CourseListPageView,
    RoadmapDetailPageView,
    RoadmapListPageView,
)

app_name = CourseWebAppNameVO.NAMESPACE.value

urlpatterns = [
    path(
        CourseWebPathVO.COURSES.value,
        CourseListPageView.as_view(),
        name=CourseWebRouteNameVO.COURSE_LIST.value,
    ),
    path(
        CourseWebPathVO.COURSE_DETAIL.value,
        CourseDetailPageView.as_view(),
        name=CourseWebRouteNameVO.COURSE_DETAIL.value,
    ),
    path(
        CourseWebPathVO.ROADMAPS.value,
        RoadmapListPageView.as_view(),
        name=CourseWebRouteNameVO.ROADMAP_LIST.value,
    ),
    path(
        CourseWebPathVO.ROADMAP_DETAIL.value,
        RoadmapDetailPageView.as_view(),
        name=CourseWebRouteNameVO.ROADMAP_DETAIL.value,
    ),
]
