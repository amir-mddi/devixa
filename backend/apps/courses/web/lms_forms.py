from __future__ import annotations

from django import forms

from backend.apps.courses.enums import (
    AssignmentStatusEnum,
    AssignmentSubmissionTypeEnum,
    AssignmentTypeEnum,
    CourseResourceTypeEnum,
    GradeCategoryEnum,
)


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class CourseSectionForm(forms.Form):
    title = forms.CharField(max_length=180, label="عنوان بخش")
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="توضیحات")
    position = forms.IntegerField(required=False, min_value=1, label="ترتیب")
    release_at = forms.DateTimeField(required=False, widget=DateTimeLocalInput(format="%Y-%m-%dT%H:%M"), input_formats=["%Y-%m-%dT%H:%M"], label="زمان انتشار")


class CourseLessonManageForm(forms.Form):
    section_id = forms.UUIDField(required=False, label="بخش")
    title = forms.CharField(max_length=180, label="عنوان درس")
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="خلاصه")
    content = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 8}), label="محتوای درس")
    video_url = forms.URLField(required=False, label="لینک ویدئو")
    duration_minutes = forms.IntegerField(required=False, min_value=0, initial=0, label="مدت (دقیقه)")
    position = forms.IntegerField(required=False, min_value=1, label="ترتیب")
    is_preview = forms.BooleanField(required=False, label="پیش‌نمایش عمومی")
    release_at = forms.DateTimeField(required=False, widget=DateTimeLocalInput(format="%Y-%m-%dT%H:%M"), input_formats=["%Y-%m-%dT%H:%M"], label="زمان انتشار")
    require_completion = forms.BooleanField(required=False, label="نیازمند علامت‌گذاری تکمیل")

    def __init__(self, *args, sections=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section_id"].widget = forms.Select(
            choices=[("", "بدون بخش")] + [(str(section.id), section.title) for section in sections]
        )


class CourseResourceForm(forms.Form):
    lesson_id = forms.UUIDField(required=False, label="درس")
    title = forms.CharField(max_length=180, label="عنوان منبع")
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="توضیحات")
    resource_type = forms.ChoiceField(choices=CourseResourceTypeEnum.choices(), label="نوع منبع")
    file = forms.FileField(required=False, label="فایل")
    external_url = forms.URLField(required=False, label="لینک")
    text_content = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 5}), label="متن/یادداشت")
    position = forms.IntegerField(required=False, min_value=1, label="ترتیب")
    release_at = forms.DateTimeField(required=False, widget=DateTimeLocalInput(format="%Y-%m-%dT%H:%M"), input_formats=["%Y-%m-%dT%H:%M"], label="زمان انتشار")

    def __init__(self, *args, lessons=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lesson_id"].widget = forms.Select(
            choices=[("", "منبع عمومی دوره")] + [(str(lesson.id), lesson.title) for lesson in lessons]
        )


class CourseAssignmentForm(forms.Form):
    lesson_id = forms.UUIDField(required=False, label="درس")
    title = forms.CharField(max_length=180, label="عنوان تمرین/پروژه")
    assignment_type = forms.ChoiceField(choices=AssignmentTypeEnum.choices(), label="نوع")
    submission_type = forms.ChoiceField(choices=AssignmentSubmissionTypeEnum.choices(), label="نوع تحویل")
    instructions = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 6}), label="شرح و دستور کار")
    attachment = forms.FileField(required=False, label="فایل صورت مسئله")
    starts_at = forms.DateTimeField(required=False, widget=DateTimeLocalInput(format="%Y-%m-%dT%H:%M"), input_formats=["%Y-%m-%dT%H:%M"], label="شروع دریافت")
    due_at = forms.DateTimeField(required=False, widget=DateTimeLocalInput(format="%Y-%m-%dT%H:%M"), input_formats=["%Y-%m-%dT%H:%M"], label="مهلت تحویل")
    allow_late_submission = forms.BooleanField(required=False, label="اجازه تحویل دیرهنگام")
    max_score = forms.DecimalField(min_value=0.01, max_digits=7, decimal_places=2, initial=100, label="سقف نمره")
    position = forms.IntegerField(required=False, min_value=1, label="ترتیب")
    status = forms.ChoiceField(choices=AssignmentStatusEnum.choices(), initial=AssignmentStatusEnum.PUBLISHED.value, label="وضعیت")

    def __init__(self, *args, lessons=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lesson_id"].widget = forms.Select(
            choices=[("", "بدون درس مشخص")] + [(str(lesson.id), lesson.title) for lesson in lessons]
        )


class CourseSubmissionForm(forms.Form):
    text_answer = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 6}), label="پاسخ متنی")
    file = forms.FileField(required=False, label="فایل تحویل")
    link_url = forms.URLField(required=False, label="لینک تحویل")


class CourseSubmissionGradeForm(forms.Form):
    score = forms.DecimalField(min_value=0, max_digits=7, decimal_places=2, label="نمره")
    feedback = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}), label="بازخورد مدرس")


class CourseGradeItemForm(forms.Form):
    student_id = forms.UUIDField(label="هنرجو")
    title = forms.CharField(max_length=180, label="عنوان نمره")
    category = forms.ChoiceField(choices=GradeCategoryEnum.choices(), label="دسته")
    score = forms.DecimalField(min_value=0, max_digits=7, decimal_places=2, label="نمره")
    max_score = forms.DecimalField(min_value=0.01, max_digits=7, decimal_places=2, initial=100, label="از")
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="یادداشت")
    is_published_to_student = forms.BooleanField(required=False, initial=True, label="نمایش به هنرجو")

    def __init__(self, *args, students=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_id"].widget = forms.Select(
            choices=[(str(item.user_id), item.user.get_full_name().strip() or item.user.username) for item in students]
        )


class CourseQuestionForm(forms.Form):
    subject = forms.CharField(max_length=180, label="موضوع سؤال")
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), label="متن سؤال")
    attachment = forms.FileField(required=False, label="پیوست")


class CourseQuestionReplyForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), label="پیام")
    attachment = forms.FileField(required=False, label="پیوست")


class CourseAnnouncementForm(forms.Form):
    title = forms.CharField(max_length=180, label="عنوان اعلان")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), label="متن اعلان")
    expires_at = forms.DateTimeField(required=False, widget=DateTimeLocalInput(format="%Y-%m-%dT%H:%M"), input_formats=["%Y-%m-%dT%H:%M"], label="پایان نمایش")
    is_pinned = forms.BooleanField(required=False, label="سنجاق‌شده")
