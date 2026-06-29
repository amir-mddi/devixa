from django.contrib import admin

from dealio.apps.courses.models import (
    Course,
    CourseCategory,
    CourseEnrollment,
    CourseLesson,
    CourseReview,
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
