from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.courses.dtos import (
    CourseCreateDTO,
    CourseLessonCreateDTO,
    CourseStatusUpdateDTO,
    CourseUpdateDTO,
    ReviewCreateDTO,
    ReviewModerationDTO,
)
from dealio.apps.courses.repositories.adapters.postgres_adapter import CoursePostgresAdapter


class CourseLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = CoursePostgresAdapter()


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
