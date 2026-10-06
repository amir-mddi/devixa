from decimal import Decimal
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

import backend.apps.courses.models


BASE_FIELDS = [
    ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
    ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
    ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
    ("deleted_at", models.DateTimeField(blank=True, null=True)),
    ("is_active", models.BooleanField(blank=True, default=True)),
    ("is_deleted", models.BooleanField(default=False)),
]


def audit_fields():
    return [
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
    ]


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0003_alter_course_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseSection",
            fields=BASE_FIELDS
            + [
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True, default="")),
                ("position", models.PositiveIntegerField(default=0)),
                ("release_at", models.DateTimeField(blank=True, null=True)),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="courses.course"),
                ),
            ]
            + audit_fields(),
            options={"ordering": ["position", "created_at"]},
        ),
        migrations.AddField(
            model_name="courselesson",
            name="section",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lessons", to="courses.coursesection"),
        ),
        migrations.AddField(
            model_name="courselesson",
            name="release_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="courselesson",
            name="require_completion",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="CourseResource",
            fields=BASE_FIELDS
            + [
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True, default="")),
                ("resource_type", models.CharField(choices=[("file", "File"), ("link", "Link"), ("note", "Note")], default="file", max_length=20)),
                ("file", models.FileField(blank=True, null=True, upload_to=backend.apps.courses.models.course_resource_upload_to)),
                ("external_url", models.URLField(blank=True, default="")),
                ("text_content", models.TextField(blank=True, default="")),
                ("position", models.PositiveIntegerField(default=0)),
                ("release_at", models.DateTimeField(blank=True, null=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="courses.course")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="courses.courselesson")),
            ]
            + audit_fields(),
            options={"ordering": ["position", "created_at"]},
        ),
        migrations.CreateModel(
            name="CourseAssignment",
            fields=BASE_FIELDS
            + [
                ("title", models.CharField(max_length=180)),
                ("assignment_type", models.CharField(choices=[("exercise", "Exercise"), ("project", "Project"), ("quiz", "Quiz"), ("other", "Other")], default="exercise", max_length=20)),
                ("submission_type", models.CharField(choices=[("file", "File"), ("text", "Text"), ("link", "Link"), ("mixed", "Mixed")], default="mixed", max_length=20)),
                ("instructions", models.TextField(blank=True, default="")),
                ("attachment", models.FileField(blank=True, null=True, upload_to=backend.apps.courses.models.course_assignment_upload_to)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("allow_late_submission", models.BooleanField(default=False)),
                ("max_score", models.DecimalField(decimal_places=2, default=Decimal("100.00"), max_digits=7)),
                ("position", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")], db_index=True, default="draft", max_length=20)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="courses.course")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assignments", to="courses.courselesson")),
            ]
            + audit_fields(),
            options={"ordering": ["position", "due_at", "created_at"]},
        ),
        migrations.CreateModel(
            name="CourseSubmission",
            fields=BASE_FIELDS
            + [
                ("text_answer", models.TextField(blank=True, default="")),
                ("file", models.FileField(blank=True, null=True, upload_to=backend.apps.courses.models.course_submission_upload_to)),
                ("link_url", models.URLField(blank=True, default="")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("submitted", "Submitted"), ("late", "Late"), ("graded", "Graded"), ("returned", "Returned")], db_index=True, default="submitted", max_length=20)),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("score", models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ("feedback", models.TextField(blank=True, default="")),
                ("graded_at", models.DateTimeField(blank=True, null=True)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="courses.courseassignment")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_submissions", to=settings.AUTH_USER_MODEL)),
                ("graded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="graded_course_submissions", to=settings.AUTH_USER_MODEL)),
            ]
            + audit_fields(),
            options={"ordering": ["-submitted_at"]},
        ),
        migrations.CreateModel(
            name="CourseGradeItem",
            fields=BASE_FIELDS
            + [
                ("title", models.CharField(max_length=180)),
                ("category", models.CharField(choices=[("assignment", "Assignment"), ("project", "Project"), ("quiz", "Quiz"), ("exam", "Exam"), ("participation", "Participation"), ("manual", "Manual")], default="manual", max_length=20)),
                ("score", models.DecimalField(decimal_places=2, max_digits=7)),
                ("max_score", models.DecimalField(decimal_places=2, default=Decimal("100.00"), max_digits=7)),
                ("note", models.TextField(blank=True, default="")),
                ("is_published_to_student", models.BooleanField(default=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grade_items", to="courses.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_grade_items", to=settings.AUTH_USER_MODEL)),
            ]
            + audit_fields(),
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="CourseLessonProgress",
            fields=BASE_FIELDS
            + [
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_records", to="courses.courselesson")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_lesson_progress", to=settings.AUTH_USER_MODEL)),
            ]
            + audit_fields(),
        ),
        migrations.CreateModel(
            name="CourseAnnouncement",
            fields=BASE_FIELDS
            + [
                ("title", models.CharField(max_length=180)),
                ("message", models.TextField()),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("is_pinned", models.BooleanField(default=False)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="course_announcements", to=settings.AUTH_USER_MODEL)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="announcements", to="courses.course")),
            ]
            + audit_fields(),
            options={"ordering": ["-is_pinned", "-published_at"]},
        ),
        migrations.CreateModel(
            name="CourseQuestion",
            fields=BASE_FIELDS
            + [
                ("subject", models.CharField(max_length=180)),
                ("status", models.CharField(choices=[("open", "Open"), ("answered", "Answered"), ("closed", "Closed")], db_index=True, default="open", max_length=20)),
                ("last_message_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="courses.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_questions", to=settings.AUTH_USER_MODEL)),
            ]
            + audit_fields(),
            options={"ordering": ["-last_message_at"]},
        ),
        migrations.CreateModel(
            name="CourseQuestionMessage",
            fields=BASE_FIELDS
            + [
                ("body", models.TextField()),
                ("attachment", models.FileField(blank=True, null=True, upload_to=backend.apps.courses.models.course_resource_upload_to)),
                ("sent_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="courses.coursequestion")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_question_messages", to=settings.AUTH_USER_MODEL)),
            ]
            + audit_fields(),
            options={"ordering": ["sent_at", "created_at"]},
        ),
        migrations.AddConstraint(model_name="coursesection", constraint=models.UniqueConstraint(fields=("course", "position"), name="unique_course_section_position")),
        migrations.AddConstraint(model_name="coursesubmission", constraint=models.UniqueConstraint(fields=("assignment", "student"), name="unique_assignment_student_submission")),
        migrations.AddConstraint(model_name="courselessonprogress", constraint=models.UniqueConstraint(fields=("lesson", "student"), name="unique_lesson_student_progress")),
        migrations.AddIndex(model_name="coursesection", index=models.Index(fields=["course", "position"], name="course_section_order_idx")),
        migrations.AddIndex(model_name="courseresource", index=models.Index(fields=["course", "lesson", "position"], name="course_resource_order_idx")),
        migrations.AddIndex(model_name="courseassignment", index=models.Index(fields=["course", "status", "due_at"], name="course_assignment_due_idx")),
        migrations.AddIndex(model_name="coursesubmission", index=models.Index(fields=["student", "status"], name="submission_student_status_idx")),
        migrations.AddIndex(model_name="coursesubmission", index=models.Index(fields=["assignment", "status"], name="submission_assignment_status_idx")),
        migrations.AddIndex(model_name="coursegradeitem", index=models.Index(fields=["course", "student", "is_published_to_student"], name="course_grade_student_idx")),
        migrations.AddIndex(model_name="courselessonprogress", index=models.Index(fields=["student", "lesson"], name="lesson_progress_student_idx")),
        migrations.AddIndex(model_name="courseannouncement", index=models.Index(fields=["course", "published_at"], name="course_announcement_pub_idx")),
        migrations.AddIndex(model_name="coursequestion", index=models.Index(fields=["course", "status", "last_message_at"], name="course_question_state_idx")),
        migrations.AddIndex(model_name="coursequestion", index=models.Index(fields=["student", "last_message_at"], name="course_question_student_idx")),
        migrations.AddIndex(model_name="coursequestionmessage", index=models.Index(fields=["question", "sent_at"], name="question_message_time_idx")),
    ]
