from asgiref.sync import sync_to_async
from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.courses.dtos.web_course_dtos import (
    CourseCatalogDTO,
    CourseCategoryFilterDTO,
    CourseDetailPageDTO,
)
from backend.apps.courses.dtos.roadmap_dtos import CourseRoadmapCatalogDTO, CourseRoadmapDetailDTO
from backend.apps.courses.entities.roadmap_entities import CourseRoadmapCatalogEntity
from backend.apps.courses.enums import CourseLevelEnum
from backend.apps.courses.dtos import (
    CourseCreateDTO,
    CourseLessonCreateDTO,
    CourseStatusUpdateDTO,
    CourseUpdateDTO,
    ReviewCreateDTO,
    ReviewModerationDTO,
)
from backend.apps.courses.repositories.adapters.postgres_adapter import CoursePostgresAdapter
from backend.apps.courses.vo.roadmap_vo import (
    CourseQueryParamVO,
    CourseRoadmapCategoryVO,
    CourseRoadmapLimitVO,
    CourseRoadmapQueryParamVO,
    CourseWebCategoryFilterVO,
    CourseWebFilterKeyVO,
    CourseWebLimitVO,
    CourseWebLevelFilterVO,
    CourseWebLevelLabelVO,
)


class CourseLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = CoursePostgresAdapter()



    async def list_published_courses_async(self, filters: dict):
        return self.list_published_courses(filters)

    async def get_published_course_async(self, course_id_or_slug):
        return await sync_to_async(
            self.get_published_course,
            thread_sensitive=True,
        )(course_id_or_slug)

    async def list_user_enrollments_async(self, user):
        return self.list_user_enrollments(user)

    async def list_approved_reviews_async(self, course_id_or_slug):
        return self.list_approved_reviews(course_id_or_slug)

    async def submit_review_async(self, user, dto: ReviewCreateDTO):
        return await sync_to_async(
            self.submit_review,
            thread_sensitive=True,
        )(user=user, dto=dto)

    async def list_reviews_for_admin_async(self, status: str | None = None):
        return self.list_reviews_for_admin(status=status)

    async def moderate_review_async(self, admin_user, dto: ReviewModerationDTO):
        return await sync_to_async(
            self.moderate_review,
            thread_sensitive=True,
        )(admin_user=admin_user, dto=dto)

    def list_learning_roadmaps(self, filters: dict | None = None) -> CourseRoadmapCatalogDTO:
        normalized_filters = filters or {}
        selected_category = (
            normalized_filters.get(CourseRoadmapQueryParamVO.CATEGORY.value)
            or CourseRoadmapCategoryVO.ALL.value
        )
        search = (normalized_filters.get(CourseRoadmapQueryParamVO.SEARCH.value) or "").strip().lower()

        roadmaps = CourseRoadmapCatalogEntity.all()

        if selected_category != CourseRoadmapCategoryVO.ALL.value:
            roadmaps = tuple(
                roadmap for roadmap in roadmaps if roadmap.category == selected_category
            )

        if search:
            roadmaps = tuple(
                roadmap
                for roadmap in roadmaps
                if search in roadmap.title.lower()
                or search in roadmap.description.lower()
                or search in roadmap.category_label.lower()
                or any(search in term.lower() for term in roadmap.related_course_search_terms)
            )

        return CourseRoadmapCatalogDTO(
            roadmaps=roadmaps,
            selected_category=selected_category,
            search=search,
        )

    def find_learning_roadmap(self, slug: str):
        normalized_slug = (slug or "").strip().lower()
        for roadmap in CourseRoadmapCatalogEntity.all():
            if roadmap.slug == normalized_slug:
                return roadmap
        return None

    def get_learning_roadmap_detail(self, slug: str) -> CourseRoadmapDetailDTO | None:
        roadmap = self.find_learning_roadmap(slug)
        if not roadmap:
            return None

        return CourseRoadmapDetailDTO(
            roadmap=roadmap,
            related_courses=self._related_courses_for_roadmap(roadmap),
        )

    def _related_courses_for_roadmap(self, roadmap):
        related_courses = []
        seen_course_ids = set()

        for search_term in roadmap.related_course_search_terms:
            queryset = self.list_published_courses(filters={CourseRoadmapQueryParamVO.SEARCH.value: search_term})
            for course in queryset[: CourseRoadmapLimitVO.RELATED_COURSES_LIMIT.value]:
                if course.id in seen_course_ids:
                    continue

                seen_course_ids.add(course.id)
                related_courses.append(course)

                if len(related_courses) >= CourseRoadmapLimitVO.RELATED_COURSES_LIMIT.value:
                    return related_courses

        return related_courses


    def list_published_course_categories(self):
        return self.postgres_adapter.list_published_course_categories()

    def build_course_catalog(self, filters: dict | None = None) -> CourseCatalogDTO:
        normalized_filters = filters or {}
        selected_category = (
            normalized_filters.get(CourseQueryParamVO.CATEGORY.value)
            or CourseWebCategoryFilterVO.ALL_VALUE.value
        )
        selected_level = (
            normalized_filters.get(CourseQueryParamVO.LEVEL.value)
            or CourseWebLevelFilterVO.ALL_VALUE.value
        )
        search = (normalized_filters.get(CourseQueryParamVO.SEARCH.value) or "").strip()

        courses = list(
            self.list_published_courses(
                filters={
                    CourseQueryParamVO.CATEGORY.value: selected_category,
                    CourseQueryParamVO.LEVEL.value: selected_level,
                    CourseQueryParamVO.SEARCH.value: search,
                }
            )
        )

        categories = [
            CourseCategoryFilterDTO(
                value=CourseWebCategoryFilterVO.ALL_VALUE.value,
                label=CourseWebCategoryFilterVO.ALL_LABEL.value,
            )
        ]
        categories.extend(
            CourseCategoryFilterDTO(value=category.slug, label=category.title)
            for category in self.list_published_course_categories()
        )

        return CourseCatalogDTO(
            courses=tuple(courses),
            categories=tuple(categories),
            selected_category=selected_category,
            selected_level=selected_level,
            search=search,
        )

    def list_home_featured_courses(self):
        return tuple(self.postgres_adapter.list_featured_courses(CourseWebLimitVO.HOME_FEATURED_COURSES.value))

    def list_home_featured_roadmaps(self):
        return CourseRoadmapCatalogEntity.all()[: CourseWebLimitVO.HOME_FEATURED_ROADMAPS.value]

    def get_course_detail_page(self, course_id_or_slug) -> CourseDetailPageDTO:
        course = self.get_published_course(course_id_or_slug)
        return CourseDetailPageDTO(
            course=course,
            reviews=tuple(self.list_approved_reviews(course.id)[: CourseWebLimitVO.COURSE_DETAIL_REVIEWS.value]),
            related_courses=tuple(
                self.postgres_adapter.list_related_courses(
                    course=course,
                    limit=CourseWebLimitVO.COURSE_RELATED_COURSES.value,
                )
            ),
        )

    @staticmethod
    def course_level_filters():
        return (
            {
                CourseWebFilterKeyVO.VALUE.value: CourseWebLevelFilterVO.ALL_VALUE.value,
                CourseWebFilterKeyVO.LABEL.value: CourseWebLevelFilterVO.ALL_LABEL.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseLevelEnum.BEGINNER.value,
                CourseWebFilterKeyVO.LABEL.value: CourseWebLevelLabelVO.BEGINNER.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseLevelEnum.INTERMEDIATE.value,
                CourseWebFilterKeyVO.LABEL.value: CourseWebLevelLabelVO.INTERMEDIATE.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseLevelEnum.ADVANCED.value,
                CourseWebFilterKeyVO.LABEL.value: CourseWebLevelLabelVO.ADVANCED.value,
            },
            {
                CourseWebFilterKeyVO.VALUE.value: CourseLevelEnum.ALL_LEVELS.value,
                CourseWebFilterKeyVO.LABEL.value: CourseWebLevelLabelVO.ALL_LEVELS.value,
            },
        )

    def list_courses_for_admin(self, filters: dict | None = None):
        return self.postgres_adapter.list_courses_for_admin(filters or {})

    def get_course_for_admin(self, course_id_or_slug):
        return self.postgres_adapter.get_course_for_admin(course_id_or_slug)

    def create_course(self, admin_user, dto: CourseCreateDTO):
        return self.postgres_adapter.create_course(admin_user=admin_user, dto=dto)

    def update_course(self, admin_user, dto: CourseUpdateDTO):
        return self.postgres_adapter.update_course(admin_user=admin_user, dto=dto)

    def update_course_status(self, admin_user, dto: CourseStatusUpdateDTO):
        return self.postgres_adapter.update_course_status(
            admin_user=admin_user,
            course_id=dto.course_id,
            status=dto.status,
        )

    def delete_course(self, admin_user, course_id):
        return self.postgres_adapter.delete_course(admin_user=admin_user, course_id=course_id)

    def create_lesson(self, admin_user, dto: CourseLessonCreateDTO):
        return self.postgres_adapter.create_lesson(admin_user=admin_user, dto=dto)

    def list_published_courses(self, filters: dict):
        return self.postgres_adapter.list_published_courses(filters)

    def get_published_course(self, course_id_or_slug):
        return self.postgres_adapter.get_published_course(course_id_or_slug)

    def list_user_enrollments(self, user):
        return self.postgres_adapter.list_user_enrollments(user)

    def list_user_reviews(self, user):
        return self.postgres_adapter.list_user_reviews(user)

    def submit_review(self, user, dto: ReviewCreateDTO):
        return self.postgres_adapter.create_or_update_review(user=user, dto=dto)

    def list_approved_reviews(self, course_id_or_slug):
        return self.postgres_adapter.list_approved_reviews(course_id_or_slug)

    def list_reviews_for_admin(self, status: str | None = None):
        return self.postgres_adapter.list_reviews_for_admin(status=status)

    def moderate_review(self, admin_user, dto: ReviewModerationDTO):
        return self.postgres_adapter.moderate_review(
            review_id=dto.review_id,
            admin_user=admin_user,
            status=dto.status.value if hasattr(dto.status, "value") else dto.status,
            admin_note=dto.admin_note,
        )
