from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers

from dealio.apps.courses.enums import CourseStatusEnum, ReviewStatusEnum
from dealio.apps.courses.models import (
    Course,
    CourseCategory,
    CourseEnrollment,
    CourseLesson,
    CourseReview,
)
from dealio.apps.shared.serializers import BaseSerializerModel

User = get_user_model()


class CourseCategorySerializer(BaseSerializerModel):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta(BaseSerializerModel.Meta):
        model = CourseCategory
        fields = ["title", "slug", "description", "position"]
        read_only_fields = ["slug"]


class CourseLessonSerializer(BaseSerializerModel):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta(BaseSerializerModel.Meta):
        model = CourseLesson
        fields = [
            "course",
            "title",
            "slug",
            "description",
            "content",
            "video_url",
            "duration_minutes",
            "position",
            "is_preview",
        ]
        read_only_fields = ["slug"]


class CourseLessonPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = ["id", "title", "slug", "description", "duration_minutes", "position", "is_preview"]


class CourseListSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    instructor = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "thumbnail",
            "price",
            "currency",
            "level",
            "duration_minutes",
            "is_featured",
            "published_at",
            "category",
            "instructor",
            "average_rating",
            "reviews_count",
        ]

    def get_instructor(self, obj):
        return {
            "id": str(obj.instructor_id),
            "username": getattr(obj.instructor, "username", ""),
            "full_name": f"{getattr(obj.instructor, 'first_name', '')} {getattr(obj.instructor, 'last_name', '')}".strip(),
        }

    def get_average_rating(self, obj):
        value = getattr(obj, "average_rating", None)
        if value is None:
            value = obj.reviews.filter(status=ReviewStatusEnum.APPROVED.value, is_deleted=False).aggregate(avg=Avg("rating"))["avg"]
        return round(float(value), 2) if value is not None else None

    def get_reviews_count(self, obj):
        value = getattr(obj, "reviews_count", None)
        if value is None:
            value = obj.reviews.filter(status=ReviewStatusEnum.APPROVED.value, is_deleted=False).count()
        return value


class CourseDetailSerializer(CourseListSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["description", "lessons"]

    def get_lessons(self, obj):
        lessons = obj.lessons.filter(is_active=True, is_deleted=False).order_by("position")
        request = self.context.get("request")
        user = getattr(request, "user", None)
        owns_course = bool(
            user
            and user.is_authenticated
            and obj.enrollments.filter(user=user, is_deleted=False, status="active").exists()
        )
        if not owns_course:
            lessons = lessons.filter(is_preview=True)
        return CourseLessonPublicSerializer(lessons, many=True).data


class CourseAdminSerializer(BaseSerializerModel):
    slug = serializers.SlugField(required=False, allow_blank=True)
    instructor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta(BaseSerializerModel.Meta):
        model = Course
        fields = [
            "category",
            "instructor",
            "title",
            "slug",
            "short_description",
            "description",
            "thumbnail",
            "price",
            "currency",
            "level",
            "status",
            "duration_minutes",
            "is_featured",
            "published_at",
        ]
        read_only_fields = ["published_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if "instructor" not in validated_data and request and request.user.is_authenticated:
            validated_data["instructor"] = request.user
        return super().create(validated_data)


class CourseReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = CourseReview
        fields = ["id", "rating", "title", "comment", "user", "created_at"]

    def get_user(self, obj):
        return {
            "id": str(obj.user_id),
            "username": getattr(obj.user, "username", ""),
        }


class CourseReviewCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField(write_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=180, required=False, allow_blank=True)
    comment = serializers.CharField(allow_blank=False)


class CourseReviewModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[ReviewStatusEnum.APPROVED.value, ReviewStatusEnum.REJECTED.value])
    admin_note = serializers.CharField(required=False, allow_blank=True)


class CourseReviewAdminSerializer(BaseSerializerModel):
    course = CourseListSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    reviewed_by = serializers.SerializerMethodField()

    class Meta(BaseSerializerModel.Meta):
        model = CourseReview
        fields = [
            "course",
            "user",
            "rating",
            "title",
            "comment",
            "status",
            "reviewed_by",
            "reviewed_at",
            "admin_note",
        ]
        read_only_fields = ["course", "user", "reviewed_by", "reviewed_at"]

    def get_user(self, obj):
        return {"id": str(obj.user_id), "username": getattr(obj.user, "username", "")}

    def get_reviewed_by(self, obj):
        if not obj.reviewed_by_id:
            return None
        return {"id": str(obj.reviewed_by_id), "username": getattr(obj.reviewed_by, "username", "")}


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ["id", "course", "status", "enrolled_at", "source_order_number"]
