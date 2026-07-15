from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("title", models.CharField(max_length=150, unique=True)),
                ("slug", models.SlugField(max_length=170, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Course category",
                "verbose_name_plural": "Course categories",
                "ordering": ["position", "title"],
            },
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("title", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("short_description", models.CharField(blank=True, default="", max_length=300)),
                ("description", models.TextField(blank=True, default="")),
                ("thumbnail", models.ImageField(blank=True, null=True, upload_to="courses/thumbnails/")),
                ("price", models.DecimalField(decimal_places=2, default="0.00", max_digits=12)),
                (
                    "currency",
                    models.CharField(
                        choices=[("irr", "Irr"), ("usd", "Usd"), ("eur", "Eur")],
                        default="irr",
                        max_length=10,
                    ),
                ),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("beginner", "Beginner"),
                            ("intermediate", "Intermediate"),
                            ("advanced", "Advanced"),
                            ("all_levels", "All_Levels"),
                        ],
                        default="all_levels",
                        max_length=30,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")],
                        db_index=True,
                        default="draft",
                        max_length=30,
                    ),
                ),
                ("duration_minutes", models.PositiveIntegerField(default=0)),
                ("is_featured", models.BooleanField(default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="courses",
                        to="courses.coursecategory",
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="instructed_courses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CourseLesson",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("title", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=220)),
                ("description", models.TextField(blank=True, default="")),
                ("content", models.TextField(blank=True, default="")),
                ("video_url", models.URLField(blank=True, default="")),
                ("duration_minutes", models.PositiveIntegerField(default=0)),
                ("position", models.PositiveIntegerField(default=0)),
                ("is_preview", models.BooleanField(default=False)),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="courses.course"),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["position", "created_at"]},
        ),
        migrations.CreateModel(
            name="CourseEnrollment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("refunded", "Refunded"), ("cancelled", "Cancelled")],
                        db_index=True,
                        default="active",
                        max_length=30,
                    ),
                ),
                ("enrolled_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("source_order_number", models.CharField(blank=True, default="", max_length=60)),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="courses.course"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_enrollments", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-enrolled_at"]},
        ),
        migrations.CreateModel(
            name="CourseReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("title", models.CharField(blank=True, default="", max_length=180)),
                ("comment", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        db_index=True,
                        default="pending",
                        max_length=30,
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("admin_note", models.TextField(blank=True, default="")),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="courses.course"),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="moderated_course_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_reviews", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="course", index=models.Index(fields=["status", "is_active", "is_deleted"], name="course_public_idx")),
        migrations.AddIndex(model_name="course", index=models.Index(fields=["slug"], name="course_slug_idx")),
        migrations.AddConstraint(model_name="courselesson", constraint=models.UniqueConstraint(fields=("course", "slug"), name="unique_course_lesson_slug")),
        migrations.AddConstraint(model_name="courselesson", constraint=models.UniqueConstraint(fields=("course", "position"), name="unique_course_lesson_position")),
        migrations.AddConstraint(model_name="courseenrollment", constraint=models.UniqueConstraint(fields=("user", "course"), name="unique_user_course_enrollment")),
        migrations.AddIndex(model_name="courseenrollment", index=models.Index(fields=["user", "status"], name="enrollment_user_status_idx")),
        migrations.AddConstraint(model_name="coursereview", constraint=models.UniqueConstraint(fields=("course", "user"), name="unique_user_course_review")),
        migrations.AddIndex(model_name="coursereview", index=models.Index(fields=["course", "status"], name="review_course_status_idx")),
    ]
