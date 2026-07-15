from backend.apps.admin_panel.repositories import AdminPanelRepository
from backend.apps.courses.dtos import (
    CourseCreateDTO,
    CourseLessonCreateDTO,
    CourseUpdateDTO,
)
from backend.apps.courses.repositories.logic import CourseLogicRepository


class AdminCourseLogic:
    def __init__(
        self,
        course_logic: CourseLogicRepository | None = None,
        repository: AdminPanelRepository | None = None,
    ):
        self.course_logic = course_logic or CourseLogicRepository()
        self.repository = repository or AdminPanelRepository()

    def list_courses(self, filters: dict | None = None):
        return self.course_logic.list_courses_for_admin(filters=filters or {})

    def get_course(self, course_id):
        return self.course_logic.get_course_for_admin(course_id)

    def list_categories(self):
        return self.repository.list_course_categories()

    def create_course(self, *, actor, data: dict, thumbnail=None):
        course = self.course_logic.create_course(
            admin_user=actor,
            dto=CourseCreateDTO(**data),
        )
        return self.repository.update_course_thumbnail(
            course=course,
            thumbnail=thumbnail,
            actor=actor,
        )

    def update_course(self, *, actor, course_id, data: dict, thumbnail=None):
        course = self.course_logic.update_course(
            admin_user=actor,
            dto=CourseUpdateDTO(course_id=course_id, **data),
        )
        return self.repository.update_course_thumbnail(
            course=course,
            thumbnail=thumbnail,
            actor=actor,
        )

    def update_status(self, *, actor, course_id, status: str):
        from backend.apps.courses.dtos import CourseStatusUpdateDTO

        return self.course_logic.update_course_status(
            admin_user=actor,
            dto=CourseStatusUpdateDTO(course_id=course_id, status=status),
        )

    def delete_course(self, *, actor, course_id):
        return self.course_logic.delete_course(admin_user=actor, course_id=course_id)

    def create_lesson(self, *, actor, course_id, data: dict):
        return self.course_logic.create_lesson(
            admin_user=actor,
            dto=CourseLessonCreateDTO(course_id=course_id, **data),
        )
