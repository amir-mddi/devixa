from django.contrib import admin

from backend.apps.courses.models import (
    Course,
    CourseCategory,
    CourseEnrollment,
    CourseLesson,
    CourseReview,
    CourseSection,
    CourseResource,
    CourseAssignment,
    CourseSubmission,
    CourseGradeItem,
    CourseLessonProgress,
    CourseAnnouncement,
    CourseQuestion,
    CourseQuestionMessage,
)


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "position", "is_active")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


class CourseLessonInline(admin.TabularInline):
    model = CourseLesson
    extra = 0
    fields = ("title", "slug", "position", "duration_minutes", "is_preview", "is_active")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "price", "currency", "level", "instructor", "published_at", "is_active")
    list_filter = ("status", "level", "currency", "is_featured", "is_active")
    search_fields = ("title", "slug", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CourseLessonInline]


@admin.register(CourseLesson)
class CourseLessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "position", "duration_minutes", "is_preview", "is_active")
    list_filter = ("is_preview", "is_active")
    search_fields = ("title", "course__title")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "enrolled_at", "source_order_number")
    list_filter = ("status", "enrolled_at")
    search_fields = ("user__username", "user__email", "course__title", "source_order_number")


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "rating", "status", "reviewed_by", "reviewed_at", "created_at")
    list_filter = ("status", "rating", "created_at")
    search_fields = ("course__title", "user__username", "title", "comment")
    readonly_fields = ("reviewed_at",)


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "position", "release_at", "is_active")
    list_filter = ("is_active", "release_at")
    search_fields = ("title", "course__title")


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "lesson", "resource_type", "position", "release_at")
    list_filter = ("resource_type", "release_at", "is_active")
    search_fields = ("title", "description", "course__title", "lesson__title")


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "assignment_type", "status", "due_at", "max_score", "allow_late_submission")
    list_filter = ("assignment_type", "status", "allow_late_submission", "due_at")
    search_fields = ("title", "instructions", "course__title")


@admin.register(CourseSubmission)
class CourseSubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "submitted_at", "score", "graded_at")
    list_filter = ("status", "submitted_at", "graded_at")
    search_fields = ("assignment__title", "student__username", "student__email")
    readonly_fields = ("submitted_at", "graded_at")


@admin.register(CourseGradeItem)
class CourseGradeItemAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "student", "category", "score", "max_score", "is_published_to_student")
    list_filter = ("category", "is_published_to_student")
    search_fields = ("title", "course__title", "student__username", "student__email")


@admin.register(CourseLessonProgress)
class CourseLessonProgressAdmin(admin.ModelAdmin):
    list_display = ("lesson", "student", "completed_at")
    list_filter = ("completed_at",)
    search_fields = ("lesson__title", "student__username", "student__email")


@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "author", "published_at", "expires_at", "is_pinned")
    list_filter = ("is_pinned", "published_at", "expires_at")
    search_fields = ("title", "message", "course__title", "author__username")


@admin.register(CourseQuestion)
class CourseQuestionAdmin(admin.ModelAdmin):
    list_display = ("subject", "course", "student", "status", "last_message_at", "closed_at")
    list_filter = ("status", "last_message_at")
    search_fields = ("subject", "course__title", "student__username", "student__email")


@admin.register(CourseQuestionMessage)
class CourseQuestionMessageAdmin(admin.ModelAdmin):
    list_display = ("question", "sender", "sent_at")
    list_filter = ("sent_at",)
    search_fields = ("question__subject", "sender__username", "body")
