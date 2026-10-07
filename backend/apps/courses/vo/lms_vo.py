from enum import StrEnum


class CourseLMSMessageVO(StrEnum):
    CLASSROOM_ACCESS_REQUIRED = "برای ورود به کلاس باید در این دوره ثبت‌نام فعال داشته باشید."
    INSTRUCTOR_ACCESS_REQUIRED = "فقط مدرس این دوره یا مدیر می‌تواند این عملیات را انجام دهد."
    COURSE_DETAILS_UPDATED = "اطلاعات آموزشی دوره با موفقیت به‌روزرسانی شد."
    STUDENT_ACCESS_REQUIRED = "این عملیات فقط برای هنرجوی ثبت‌نام‌شده در دوره قابل انجام است."
    COURSE_NOT_FOUND = "دوره مورد نظر پیدا نشد."
    LESSON_NOT_FOUND = "درس مورد نظر پیدا نشد."
    SECTION_NOT_FOUND = "بخش مورد نظر پیدا نشد."
    RESOURCE_NOT_FOUND = "فایل آموزشی مورد نظر پیدا نشد."
    ASSIGNMENT_NOT_FOUND = "تمرین یا پروژه مورد نظر پیدا نشد."
    SUBMISSION_NOT_FOUND = "تحویل مورد نظر پیدا نشد."
    QUESTION_NOT_FOUND = "گفت‌وگوی مورد نظر پیدا نشد."
    FILE_NOT_AVAILABLE = "فایل مورد نظر در دسترس نیست."
    ASSIGNMENT_NOT_STARTED = "زمان ارسال این تمرین هنوز شروع نشده است."
    ASSIGNMENT_DEADLINE_PASSED = "مهلت تحویل این تمرین به پایان رسیده و ارسال جدید بسته شده است."
    ASSIGNMENT_CLOSED = "این تمرین برای تحویل فعال نیست."
    SUBMISSION_EMPTY = "حداقل یک پاسخ متنی، فایل یا لینک باید ارسال شود."
    SUBMISSION_TYPE_INVALID = "نوع پاسخ با تنظیمات این تمرین سازگار نیست."
    SCORE_OUT_OF_RANGE = "نمره نمی‌تواند کمتر از صفر یا بیشتر از سقف نمره باشد."
    QUESTION_CLOSED = "این گفت‌وگو بسته شده است."
    LESSON_SAVED = "درس با موفقیت ذخیره شد."
    SECTION_CREATED = "بخش جدید کلاس ایجاد شد."
    RESOURCE_CREATED = "فایل یا منبع آموزشی با موفقیت اضافه شد."
    ASSIGNMENT_CREATED = "تمرین/پروژه با موفقیت ایجاد شد."
    SUBMISSION_SAVED = "پاسخ شما با موفقیت ثبت شد."
    SUBMISSION_GRADED = "نمره و بازخورد با موفقیت ثبت شد."
    GRADE_CREATED = "نمره با موفقیت برای هنرجو ثبت شد."
    QUESTION_CREATED = "سؤال شما برای مدرس ارسال شد."
    QUESTION_REPLIED = "پیام جدید در گفت‌وگو ثبت شد."
    ANNOUNCEMENT_CREATED = "اعلان کلاس منتشر شد."
    PROGRESS_UPDATED = "وضعیت پیشرفت درس به‌روزرسانی شد."
    INVALID_FORM = "لطفاً خطاهای فرم را بررسی کنید."
    RESOURCE_LINK_REQUIRED = "برای منبع از نوع لینک، آدرس معتبر وارد کنید."
    RESOURCE_TEXT_REQUIRED = "برای یادداشت آموزشی، متن محتوا را وارد کنید."
    INVALID_DEADLINE = "زمان تحویل باید بعد از زمان شروع باشد."
    INVALID_MAX_SCORE = "سقف نمره باید بزرگ‌تر از صفر باشد."
    STUDENT_NOT_ENROLLED = "هنرجوی انتخاب‌شده ثبت‌نام فعال در این دوره ندارد."
    QUESTION_BODY_REQUIRED = "متن سؤال یا پیام نمی‌تواند خالی باشد."
    FILE_TOO_LARGE = "حجم فایل بیشتر از حد مجاز کلاس است."
    FILE_TYPE_NOT_ALLOWED = "پسوند این فایل برای کلاس مجاز نیست."
    HTTPS_LINK_REQUIRED = "لینک باید یک آدرس عمومی امن با HTTPS باشد."


class CourseLMSTemplateVO(StrEnum):
    CLASSROOM = "web/courses/classroom.html"
    INSTRUCTOR_PANEL = "web/courses/instructor_classroom.html"
    QUESTION_DETAIL = "web/courses/question_detail.html"


class CourseLMSRouteNameVO(StrEnum):
    CLASSROOM = "classroom"
    INSTRUCTOR_PANEL = "instructor_panel"
    SECTION_CREATE = "section_create"
    LESSON_CREATE = "lesson_create"
    LESSON_EDIT = "lesson_edit"
    RESOURCE_CREATE = "resource_create"
    ASSIGNMENT_CREATE = "assignment_create"
    SUBMISSION_CREATE = "submission_create"
    SUBMISSION_GRADE = "submission_grade"
    GRADE_CREATE = "grade_create"
    QUESTION_CREATE = "question_create"
    QUESTION_DETAIL = "question_detail"
    QUESTION_REPLY = "question_reply"
    ANNOUNCEMENT_CREATE = "announcement_create"
    LESSON_PROGRESS = "lesson_progress"
    RESOURCE_DOWNLOAD = "resource_download"
    ASSIGNMENT_DOWNLOAD = "assignment_download"
    SUBMISSION_DOWNLOAD = "submission_download"
    QUESTION_ATTACHMENT_DOWNLOAD = "question_attachment_download"


class CourseLMSLimitVO:
    ANNOUNCEMENTS = 20
    QUESTIONS = 30
    BOT_ASSIGNMENTS = 8
    BOT_GRADES = 10


class CourseLMSFileVO:
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = frozenset({
        ".pdf", ".zip", ".rar", ".7z", ".txt", ".md", ".csv",
        ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
        ".jpg", ".jpeg", ".png", ".webp", ".gif",
        ".py", ".ipynb", ".json", ".xml", ".yaml", ".yml",
        ".mp3", ".m4a", ".mp4", ".webm",
    })
