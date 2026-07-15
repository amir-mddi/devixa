from __future__ import annotations

from django.http import Http404
from django.views.generic import TemplateView
from rest_framework.exceptions import NotFound

from backend.apps.courses.repositories.logic import CourseLogicRepository
from backend.apps.courses.vo.roadmap_vo import (
    CourseRoadmapCategoryLabelVO,
    CourseRoadmapCategoryVO,
    CourseRoadmapMessageVO,
    CourseWebContextKeyVO,
    CourseWebFilterKeyVO,
    CourseWebMessageVO,
    CourseWebTemplateVO,
    CourseWebUrlKwargVO,
)


class CourseWebRepositoryMixin:
    logic_repository_class = CourseLogicRepository


class CourseListPageView(CourseWebRepositoryMixin, TemplateView):
    template_name = CourseWebTemplateVO.COURSE_LIST.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logic = self.logic_repository_class()
        context.update(
            {
                CourseWebContextKeyVO.CATALOG.value: logic.build_course_catalog(filters=self.request.GET),
                CourseWebContextKeyVO.LEVEL_FILTERS.value: logic.course_level_filters(),
                CourseWebContextKeyVO.EMPTY_MESSAGE.value: CourseWebMessageVO.EMPTY_LIST.value,
            }
        )
        return context


class CourseDetailPageView(CourseWebRepositoryMixin, TemplateView):
    template_name = CourseWebTemplateVO.COURSE_DETAIL.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            detail = self.logic_repository_class().get_course_detail_page(
                course_id_or_slug=kwargs.get(CourseWebUrlKwargVO.SLUG.value)
            )
        except NotFound as exc:
            raise Http404(CourseWebMessageVO.COURSE_NOT_FOUND.value) from exc

        context.update(
            {
                CourseWebContextKeyVO.COURSE_DETAIL.value: detail,
                CourseWebContextKeyVO.COURSE.value: detail.course,
                CourseWebContextKeyVO.REVIEWS.value: detail.reviews,
                CourseWebContextKeyVO.RELATED_COURSES.value: detail.related_courses,
                CourseWebContextKeyVO.RELATED_COURSES_EMPTY_MESSAGE.value: CourseWebMessageVO.RELATED_COURSES_EMPTY.value,
                CourseWebContextKeyVO.REVIEWS_EMPTY_MESSAGE.value: CourseWebMessageVO.REVIEWS_EMPTY.value,
            }
        )
        return context


class RoadmapPageContextMixin(CourseWebRepositoryMixin):
    @staticmethod
    def category_filters() -> tuple[dict[str, str], ...]:
        return (
            {
                CourseWebFilterKeyVO.VALUE.value: CourseRoadmapCategoryVO.ALL.value,
                CourseWebFilterKeyVO.LABEL.value: CourseRoadmapCategoryLabelVO.ALL.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseRoadmapCategoryVO.FRONTEND.value,
                CourseWebFilterKeyVO.LABEL.value: CourseRoadmapCategoryLabelVO.FRONTEND.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseRoadmapCategoryVO.BACKEND.value,
                CourseWebFilterKeyVO.LABEL.value: CourseRoadmapCategoryLabelVO.BACKEND.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseRoadmapCategoryVO.FULLSTACK.value,
                CourseWebFilterKeyVO.LABEL.value: CourseRoadmapCategoryLabelVO.FULLSTACK.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseRoadmapCategoryVO.AI.value,
                CourseWebFilterKeyVO.LABEL.value: CourseRoadmapCategoryLabelVO.AI.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseRoadmapCategoryVO.FREELANCER.value,
                CourseWebFilterKeyVO.LABEL.value: CourseRoadmapCategoryLabelVO.FREELANCER.value,
            },
        )


class RoadmapListPageView(RoadmapPageContextMixin, TemplateView):
    template_name = CourseWebTemplateVO.ROADMAP_LIST.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        catalog = self.logic_repository_class().list_learning_roadmaps(filters=self.request.GET)
        context.update(
            {
                CourseWebContextKeyVO.CATALOG.value: catalog,
                CourseWebContextKeyVO.CATEGORY_FILTERS.value: self.category_filters(),
                CourseWebContextKeyVO.EMPTY_MESSAGE.value: CourseRoadmapMessageVO.EMPTY_LIST.value,
            }
        )
        return context


class RoadmapDetailPageView(RoadmapPageContextMixin, TemplateView):
    template_name = CourseWebTemplateVO.ROADMAP_DETAIL.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = self.logic_repository_class().get_learning_roadmap_detail(
            slug=kwargs.get(CourseWebUrlKwargVO.SLUG.value)
        )
        if detail is None:
            raise Http404(CourseRoadmapMessageVO.NOT_FOUND.value)

        context.update(
            {
                CourseWebContextKeyVO.DETAIL.value: detail,
                CourseWebContextKeyVO.ROADMAP.value: detail.roadmap,
                CourseWebContextKeyVO.RELATED_COURSES_EMPTY_MESSAGE.value: CourseRoadmapMessageVO.RELATED_COURSES_EMPTY.value,
            }
        )
        return context
