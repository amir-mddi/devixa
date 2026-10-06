from __future__ import annotations

from django.urls import path

from backend.apps.courses.vo.roadmap_vo import (
    CourseWebAppNameVO,
    CourseWebPathVO,
    CourseWebRouteNameVO,
)
from backend.apps.courses.web.views import (
    CourseDetailPageView,
    CourseListPageView,
    RoadmapDetailPageView,
    RoadmapListPageView,
)
from backend.apps.courses.web.lms_views import (
    AssignmentDownloadView,
    CourseAnnouncementCreateView,
    CourseAssignmentCreateView,
    CourseClassroomPageView,
    CourseGradeCreateView,
    CourseLessonProgressView,
    CourseLessonSaveView,
    CourseQuestionCreateView,
    CourseQuestionDetailView,
    CourseQuestionReplyView,
    CourseResourceCreateView,
    CourseSectionCreateView,
    CourseSubmissionCreateView,
    CourseSubmissionGradeView,
    InstructorClassroomPageView,
    QuestionAttachmentDownloadView,
    ResourceDownloadView,
    SubmissionDownloadView,
)

app_name = CourseWebAppNameVO.NAMESPACE.value

urlpatterns = [
    path(CourseWebPathVO.COURSES.value, CourseListPageView.as_view(), name=CourseWebRouteNameVO.COURSE_LIST.value),
    path(CourseWebPathVO.COURSE_DETAIL.value, CourseDetailPageView.as_view(), name=CourseWebRouteNameVO.COURSE_DETAIL.value),
    path("courses/<slug:slug>/classroom/", CourseClassroomPageView.as_view(), name="classroom"),
    path("courses/<slug:slug>/classroom/instructor/", InstructorClassroomPageView.as_view(), name="instructor_panel"),
    path("courses/<slug:slug>/classroom/sections/create/", CourseSectionCreateView.as_view(), name="section_create"),
    path("courses/<slug:slug>/classroom/lessons/create/", CourseLessonSaveView.as_view(), name="lesson_create"),
    path("courses/<slug:slug>/classroom/lessons/<uuid:lesson_id>/edit/", CourseLessonSaveView.as_view(), name="lesson_edit"),
    path("courses/<slug:slug>/classroom/resources/create/", CourseResourceCreateView.as_view(), name="resource_create"),
    path("courses/<slug:slug>/classroom/assignments/create/", CourseAssignmentCreateView.as_view(), name="assignment_create"),
    path("courses/<slug:slug>/classroom/assignments/<uuid:assignment_id>/submit/", CourseSubmissionCreateView.as_view(), name="submission_create"),
    path("courses/<slug:slug>/classroom/submissions/<uuid:submission_id>/grade/", CourseSubmissionGradeView.as_view(), name="submission_grade"),
    path("courses/<slug:slug>/classroom/grades/create/", CourseGradeCreateView.as_view(), name="grade_create"),
    path("courses/<slug:slug>/classroom/questions/create/", CourseQuestionCreateView.as_view(), name="question_create"),
    path("courses/<slug:slug>/classroom/questions/<uuid:question_id>/", CourseQuestionDetailView.as_view(), name="question_detail"),
    path("courses/<slug:slug>/classroom/questions/<uuid:question_id>/reply/", CourseQuestionReplyView.as_view(), name="question_reply"),
    path("courses/<slug:slug>/classroom/announcements/create/", CourseAnnouncementCreateView.as_view(), name="announcement_create"),
    path("courses/<slug:slug>/classroom/lessons/<uuid:lesson_id>/progress/", CourseLessonProgressView.as_view(), name="lesson_progress"),
    path("courses/classroom/files/resources/<uuid:object_id>/", ResourceDownloadView.as_view(), name="resource_download"),
    path("courses/classroom/files/assignments/<uuid:object_id>/", AssignmentDownloadView.as_view(), name="assignment_download"),
    path("courses/classroom/files/submissions/<uuid:object_id>/", SubmissionDownloadView.as_view(), name="submission_download"),
    path("courses/classroom/files/questions/<uuid:object_id>/", QuestionAttachmentDownloadView.as_view(), name="question_attachment_download"),
    path(CourseWebPathVO.ROADMAPS.value, RoadmapListPageView.as_view(), name=CourseWebRouteNameVO.ROADMAP_LIST.value),
    path(CourseWebPathVO.ROADMAP_DETAIL.value, RoadmapDetailPageView.as_view(), name=CourseWebRouteNameVO.ROADMAP_DETAIL.value),
]
