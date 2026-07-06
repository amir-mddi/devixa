from __future__ import annotations

from dealio.apps.courses.dtos.roadmap_dtos import (
    CourseRoadmapDTO,
    RoadmapProjectDTO,
    RoadmapSkillDTO,
    RoadmapStepDTO,
)
from dealio.apps.courses.vo.roadmap_vo import (
    CourseRoadmapCategoryLabelVO,
    CourseRoadmapCategoryVO,
)


class CourseRoadmapCatalogEntity:
    """Static roadmap catalog used until a dedicated Roadmap model is added."""

    @classmethod
    def all(cls) -> tuple[CourseRoadmapDTO, ...]:
        return (
            cls.frontend(),
            cls.backend(),
            cls.fullstack(),
            cls.python(),
            cls.javascript(),
            cls.react(),
            cls.laravel(),
            cls.wordpress(),
            cls.ai(),
            cls.freelancer(),
        )

    @staticmethod
    def frontend() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="frontend",
            title="Front-End",
            category=CourseRoadmapCategoryVO.FRONTEND.value,
            category_label=CourseRoadmapCategoryLabelVO.FRONTEND.value,
            description="مسیر کامل فرانت‌اند از HTML و CSS تا JavaScript، React و ساخت رابط کاربری حرفه‌ای.",
            level="مبتدی تا پیشرفته",
            duration_weeks=12,
            icon_class="devicon-html5-plain",
            related_course_search_terms=("frontend", "react", "javascript", "html", "css"),
            steps=(
                RoadmapStepDTO(1, "پایه وب", "ساختار صفحات، تگ‌های HTML، فرم‌ها و SEO پایه.", "۲ هفته", ("HTML", "Semantic HTML", "Forms")),
                RoadmapStepDTO(2, "طراحی واکنش‌گرا", "CSS مدرن، Flex/Grid، طراحی موبایل‌فرست و اصول UI.", "۳ هفته", ("CSS", "Flexbox", "Grid", "Responsive")),
                RoadmapStepDTO(3, "JavaScript کاربردی", "منطق برنامه، DOM، رویدادها، Fetch API و مدیریت State ساده.", "۳ هفته", ("JavaScript", "DOM", "Fetch")),
                RoadmapStepDTO(4, "React و پروژه", "کامپوننت، Router، فرم‌ها، اتصال API و ساخت پروژه قابل ارائه.", "۴ هفته", ("React", "Router", "API Integration")),
            ),
            skills=(
                RoadmapSkillDTO("HTML", "ساختار استاندارد صفحات وب", "devicon-html5-plain"),
                RoadmapSkillDTO("CSS", "طراحی مدرن و واکنش‌گرا", "devicon-css3-plain"),
                RoadmapSkillDTO("JavaScript", "تعاملات کاربری و منطق فرانت", "devicon-javascript-plain"),
                RoadmapSkillDTO("React", "ساخت SPA و کامپوننت‌های قابل استفاده مجدد", "devicon-react-original"),
            ),
            projects=(
                RoadmapProjectDTO("لندینگ آموزشی", "یک صفحه حرفه‌ای با CTA، FAQ و انیمیشن‌های سبک."),
                RoadmapProjectDTO("داشبورد دوره‌ها", "لیست دوره‌ها با فیلتر، جستجو و صفحه جزئیات."),
                RoadmapProjectDTO("فروشگاه کوچک", "سبد خرید، فرم سفارش و اتصال به API آزمایشی."),
            ),
        )

    @staticmethod
    def backend() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="backend",
            title="Back-End",
            category=CourseRoadmapCategoryVO.BACKEND.value,
            category_label=CourseRoadmapCategoryLabelVO.BACKEND.value,
            description="مسیر بک‌اند برای ساخت API، دیتابیس، احراز هویت، پرداخت و معماری تمیز.",
            level="مبتدی تا پیشرفته",
            duration_weeks=14,
            icon_class="devicon-django-plain",
            related_course_search_terms=("backend", "django", "python", "api", "database"),
            steps=(
                RoadmapStepDTO(1, "Python و HTTP", "مرور Python کاربردی، ساختار وب، HTTP، Request/Response و JSON.", "۲ هفته", ("Python", "HTTP", "JSON")),
                RoadmapStepDTO(2, "Django و DRF", "مدل‌ها، migrations، serializers، views، permissions و pagination.", "۴ هفته", ("Django", "DRF", "Permissions")),
                RoadmapStepDTO(3, "دیتابیس و کش", "طراحی schema، query optimization، transaction، Redis و cache.", "۳ هفته", ("PostgreSQL", "Redis", "Transactions")),
                RoadmapStepDTO(4, "معماری و Deploy", "Repository pattern، adapter، تست، Docker، CI/CD و monitoring.", "۵ هفته", ("Clean Architecture", "Docker", "Testing")),
            ),
            skills=(
                RoadmapSkillDTO("Python", "زبان اصلی پیاده‌سازی بک‌اند", "devicon-python-plain"),
                RoadmapSkillDTO("Django", "فریم‌ورک سریع و امن", "devicon-django-plain"),
                RoadmapSkillDTO("PostgreSQL", "طراحی و نگهداری دیتابیس", "devicon-postgresql-plain"),
                RoadmapSkillDTO("Docker", "اجرای قابل اعتماد سرویس‌ها", "devicon-docker-plain"),
            ),
            projects=(
                RoadmapProjectDTO("API فروش دوره", "مدیریت دوره، ثبت‌نام، سفارش و پرداخت."),
                RoadmapProjectDTO("سیستم احراز هویت", "ثبت‌نام، ورود، JWT، بازیابی رمز و نقش‌ها."),
                RoadmapProjectDTO("پنل مدیریت محتوا", "CRUD امن با سطح دسترسی و گزارش‌گیری."),
            ),
        )

    @staticmethod
    def fullstack() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="fullstack",
            title="Full-Stack",
            category=CourseRoadmapCategoryVO.FULLSTACK.value,
            category_label=CourseRoadmapCategoryLabelVO.FULLSTACK.value,
            description="مسیر فول‌استک برای ساخت محصول کامل از رابط کاربری تا API، دیتابیس و انتشار.",
            level="متوسط تا پیشرفته",
            duration_weeks=20,
            icon_class="devicon-react-original",
            related_course_search_terms=("fullstack", "react", "django", "backend", "frontend"),
            steps=(
                RoadmapStepDTO(1, "فرانت‌اند مدرن", "HTML/CSS، JavaScript و React برای ساخت رابط کاربری سریع.", "۵ هفته", ("React", "CSS", "State")),
                RoadmapStepDTO(2, "بک‌اند API", "Django/DRF، دیتابیس، احراز هویت و منطق دامنه.", "۶ هفته", ("Django", "DRF", "PostgreSQL")),
                RoadmapStepDTO(3, "اتصال دو سمت", "قرارداد API، خطاها، فرم‌ها، پرداخت و امنیت.", "۴ هفته", ("API Contract", "Auth", "Payment")),
                RoadmapStepDTO(4, "Deploy و محصول", "Docker، Nginx، CI/CD، logging و تحویل پروژه واقعی.", "۵ هفته", ("Docker", "Nginx", "Monitoring")),
            ),
            skills=(
                RoadmapSkillDTO("React", "رابط کاربری پویا", "devicon-react-original"),
                RoadmapSkillDTO("Django", "API و منطق سمت سرور", "devicon-django-plain"),
                RoadmapSkillDTO("PostgreSQL", "مدیریت داده محصول", "devicon-postgresql-plain"),
                RoadmapSkillDTO("Git", "کنترل نسخه تیمی", "devicon-git-plain"),
            ),
            projects=(
                RoadmapProjectDTO("پلتفرم دوره آنلاین", "صفحه دوره، خرید، پنل کاربر و داشبورد ادمین."),
                RoadmapProjectDTO("سیستم رزرو", "تقویم، پرداخت، وضعیت رزرو و اعلان ایمیلی."),
                RoadmapProjectDTO("SaaS کوچک", "اشتراک، سطح دسترسی، گزارش و مدیریت کاربران."),
            ),
        )

    @staticmethod
    def python() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="python",
            title="Python",
            category=CourseRoadmapCategoryVO.BACKEND.value,
            category_label=CourseRoadmapCategoryLabelVO.BACKEND.value,
            description="یادگیری Python از پایه تا نوشتن کد تمیز، تست‌پذیر و آماده ورود به Django یا اتوماسیون.",
            level="مبتدی تا متوسط",
            duration_weeks=8,
            icon_class="devicon-python-plain",
            related_course_search_terms=("python", "django", "backend"),
            steps=(
                RoadmapStepDTO(1, "مبانی زبان", "متغیرها، شرط، حلقه، تابع و کار با داده‌ها.", "۲ هفته", ("Syntax", "Functions", "Collections")),
                RoadmapStepDTO(2, "OOP و تمیزی کد", "کلاس، ارث‌بری، composition، exceptions و type hints.", "۲ هفته", ("OOP", "Type Hints", "SOLID")),
                RoadmapStepDTO(3, "فایل، API و دیتابیس", "کار با فایل، requests، JSON و اتصال به دیتابیس.", "۲ هفته", ("Files", "Requests", "SQL")),
                RoadmapStepDTO(4, "تست و پروژه", "pytest، ساخت CLI یا service کوچک و آماده‌سازی برای Django.", "۲ هفته", ("Testing", "CLI", "Packaging")),
            ),
            skills=(
                RoadmapSkillDTO("Python", "کدنویسی خوانا و قابل نگهداری", "devicon-python-plain"),
                RoadmapSkillDTO("pytest", "تست واحد و integration", "devicon-pytest-plain"),
                RoadmapSkillDTO("SQL", "ذخیره و خواندن داده", "devicon-sqlite-plain"),
                RoadmapSkillDTO("Git", "مدیریت تغییرات پروژه", "devicon-git-plain"),
            ),
            projects=(
                RoadmapProjectDTO("CLI مدیریت کارها", "ابزار خط فرمان با ذخیره‌سازی فایل یا SQLite."),
                RoadmapProjectDTO("وب اسکرپر ساده", "خواندن داده، پاک‌سازی و خروجی CSV."),
                RoadmapProjectDTO("مینی سرویس API", "یک سرویس کوچک با endpoint و تست."),
            ),
        )

    @staticmethod
    def javascript() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="javascript",
            title="JavaScript",
            category=CourseRoadmapCategoryVO.FRONTEND.value,
            category_label=CourseRoadmapCategoryLabelVO.FRONTEND.value,
            description="مسیر JavaScript برای ساخت تعاملات وب، کار با API و آماده شدن برای React یا Node.js.",
            level="مبتدی تا متوسط",
            duration_weeks=8,
            icon_class="devicon-javascript-plain",
            related_course_search_terms=("javascript", "frontend", "react", "node"),
            steps=(
                RoadmapStepDTO(1, "مبانی زبان", "متغیرها، نوع داده، تابع، scope و آرایه‌ها.", "۲ هفته", ("Syntax", "Functions", "Arrays")),
                RoadmapStepDTO(2, "DOM و رویدادها", "انتخاب عناصر، event، فرم‌ها و اعتبارسنجی.", "۲ هفته", ("DOM", "Events", "Forms")),
                RoadmapStepDTO(3, "Async و API", "Promise، async/await، fetch و مدیریت خطا.", "۲ هفته", ("Promise", "Fetch", "Errors")),
                RoadmapStepDTO(4, "پروژه و ساختار", "ماژول‌ها، bundler ساده و پروژه قابل توسعه.", "۲ هفته", ("Modules", "Architecture", "Project")),
            ),
            skills=(
                RoadmapSkillDTO("JavaScript", "منطق تعاملی وب", "devicon-javascript-plain"),
                RoadmapSkillDTO("HTML", "اتصال منطق به صفحه", "devicon-html5-plain"),
                RoadmapSkillDTO("CSS", "تعامل با کلاس‌ها و انیمیشن", "devicon-css3-plain"),
                RoadmapSkillDTO("Git", "مدیریت پروژه", "devicon-git-plain"),
            ),
            projects=(
                RoadmapProjectDTO("Todo App", "CRUD کامل سمت کلاینت با localStorage."),
                RoadmapProjectDTO("Weather App", "خواندن API و نمایش وضعیت با loading/error."),
                RoadmapProjectDTO("Catalog Filter", "جستجو، فیلتر و pagination سمت کلاینت."),
            ),
        )

    @staticmethod
    def react() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="react",
            title="React",
            category=CourseRoadmapCategoryVO.FRONTEND.value,
            category_label=CourseRoadmapCategoryLabelVO.FRONTEND.value,
            description="مسیر React برای ساخت اپلیکیشن‌های کامپوننت‌محور، سریع و قابل توسعه.",
            level="متوسط",
            duration_weeks=10,
            icon_class="devicon-react-original",
            related_course_search_terms=("react", "frontend", "javascript"),
            steps=(
                RoadmapStepDTO(1, "کامپوننت و JSX", "ساختار پروژه، props، state و event handling.", "۲ هفته", ("JSX", "Props", "State")),
                RoadmapStepDTO(2, "Hooks", "useState، useEffect، custom hook و مدیریت فرم.", "۳ هفته", ("Hooks", "Forms", "Effects")),
                RoadmapStepDTO(3, "Routing و API", "React Router، fetch/axios، loading، error و auth flow.", "۲ هفته", ("Router", "API", "Auth")),
                RoadmapStepDTO(4, "State و پروژه", "مدیریت state، بهینه‌سازی و build نهایی.", "۳ هفته", ("State Management", "Performance", "Build")),
            ),
            skills=(
                RoadmapSkillDTO("React", "ساخت UI کامپوننت‌محور", "devicon-react-original"),
                RoadmapSkillDTO("JavaScript", "منطق پایه React", "devicon-javascript-plain"),
                RoadmapSkillDTO("Vite", "ابزار سریع توسعه", "devicon-vitejs-plain"),
                RoadmapSkillDTO("CSS", "طراحی کامپوننت‌ها", "devicon-css3-plain"),
            ),
            projects=(
                RoadmapProjectDTO("پنل دوره‌ها", "فیلتر، صفحه جزئیات، login mock و protected route."),
                RoadmapProjectDTO("داشبورد فروش", "نمودار، جدول، pagination و فرم‌های پویا."),
                RoadmapProjectDTO("اپ مدیریت محتوا", "CRUD کامل با اتصال به API."),
            ),
        )

    @staticmethod
    def laravel() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="laravel",
            title="Laravel / PHP",
            category=CourseRoadmapCategoryVO.BACKEND.value,
            category_label=CourseRoadmapCategoryLabelVO.BACKEND.value,
            description="مسیر PHP و Laravel برای ساخت وب‌اپلیکیشن، پنل ادمین و API با معماری قابل نگهداری.",
            level="مبتدی تا متوسط",
            duration_weeks=12,
            icon_class="devicon-laravel-plain",
            related_course_search_terms=("php", "laravel", "backend"),
            steps=(
                RoadmapStepDTO(1, "PHP مدرن", "Syntax، OOP، composer و autoloading.", "۳ هفته", ("PHP", "OOP", "Composer")),
                RoadmapStepDTO(2, "Laravel پایه", "Route، controller، model، migration و blade.", "۳ هفته", ("Laravel", "Eloquent", "Blade")),
                RoadmapStepDTO(3, "API و Auth", "Resource، validation، policy، token و file upload.", "۳ هفته", ("API", "Auth", "Policy")),
                RoadmapStepDTO(4, "پروژه و Deploy", "Queue، cache، test و انتشار.", "۳ هفته", ("Queue", "Cache", "Deploy")),
            ),
            skills=(
                RoadmapSkillDTO("PHP", "زبان اصلی", "devicon-php-plain"),
                RoadmapSkillDTO("Laravel", "فریم‌ورک بک‌اند", "devicon-laravel-plain"),
                RoadmapSkillDTO("MySQL", "دیتابیس رایج", "devicon-mysql-plain"),
                RoadmapSkillDTO("Redis", "کش و صف", "devicon-redis-plain"),
            ),
            projects=(
                RoadmapProjectDTO("فروشگاه دوره", "دوره، سفارش، پرداخت و پنل ادمین."),
                RoadmapProjectDTO("Blog API", "نویسنده، دسته‌بندی، کامنت و جستجو."),
                RoadmapProjectDTO("سیستم تیکت", "کاربر، اپراتور، وضعیت و اعلان."),
            ),
        )

    @staticmethod
    def wordpress() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="wordpress",
            title="WordPress",
            category=CourseRoadmapCategoryVO.FREELANCER.value,
            category_label=CourseRoadmapCategoryLabelVO.FREELANCER.value,
            description="مسیر وردپرس برای طراحی سایت، شخصی‌سازی قالب و ورود سریع‌تر به پروژه‌های فریلنسری.",
            level="مبتدی تا متوسط",
            duration_weeks=8,
            icon_class="devicon-wordpress-plain",
            related_course_search_terms=("wordpress", "php", "freelancer"),
            steps=(
                RoadmapStepDTO(1, "راه‌اندازی سایت", "هاست، دامنه، نصب وردپرس و تنظیمات پایه.", "۱ هفته", ("Hosting", "Domain", "Install")),
                RoadmapStepDTO(2, "قالب و صفحه‌ساز", "قالب، child theme، Elementor و UI آماده.", "۲ هفته", ("Theme", "Elementor", "UI")),
                RoadmapStepDTO(3, "افزونه و فروشگاه", "WooCommerce، فرم، امنیت و بهینه‌سازی.", "۳ هفته", ("WooCommerce", "Forms", "Security")),
                RoadmapStepDTO(4, "تحویل پروژه", "SEO پایه، سرعت، backup و مستندسازی تحویل.", "۲ هفته", ("SEO", "Performance", "Backup")),
            ),
            skills=(
                RoadmapSkillDTO("WordPress", "مدیریت سایت", "devicon-wordpress-plain"),
                RoadmapSkillDTO("PHP", "شخصی‌سازی قالب", "devicon-php-plain"),
                RoadmapSkillDTO("CSS", "ظاهر حرفه‌ای", "devicon-css3-plain"),
                RoadmapSkillDTO("MySQL", "شناخت دیتابیس وردپرس", "devicon-mysql-plain"),
            ),
            projects=(
                RoadmapProjectDTO("وب‌سایت شرکتی", "صفحات معرفی، تماس، نمونه‌کار و SEO پایه."),
                RoadmapProjectDTO("فروشگاه کوچک", "محصول، پرداخت، حمل‌ونقل و ایمیل سفارش."),
                RoadmapProjectDTO("سایت آموزشی", "دوره، مدرس، صفحه فروش و فرم ثبت‌نام."),
            ),
        )

    @staticmethod
    def ai() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="ai",
            title="AI Engineer",
            category=CourseRoadmapCategoryVO.AI.value,
            category_label=CourseRoadmapCategoryLabelVO.AI.value,
            description="مسیر هوش مصنوعی برای شروع با Python، داده، مدل‌ها و ساخت ابزارهای کاربردی AI.",
            level="متوسط تا پیشرفته",
            duration_weeks=16,
            icon_class="devicon-python-plain",
            related_course_search_terms=("ai", "python", "machine learning", "data"),
            steps=(
                RoadmapStepDTO(1, "Python و داده", "NumPy، Pandas، پاک‌سازی داده و visualization.", "۴ هفته", ("Python", "Pandas", "Data Cleaning")),
                RoadmapStepDTO(2, "Machine Learning", "مدل‌های کلاسیک، train/test، metrics و feature engineering.", "۴ هفته", ("ML", "Metrics", "Features")),
                RoadmapStepDTO(3, "Deep Learning", "شبکه عصبی، PyTorch/TensorFlow و مدل‌های ساده.", "۴ هفته", ("Neural Networks", "PyTorch", "TensorFlow")),
                RoadmapStepDTO(4, "AI Product", "LLM API، RAG ساده، deploy و ساخت محصول کوچک.", "۴ هفته", ("LLM", "RAG", "Deploy")),
            ),
            skills=(
                RoadmapSkillDTO("Python", "زبان اصلی داده و AI", "devicon-python-plain"),
                RoadmapSkillDTO("Pandas", "پردازش داده", "devicon-pandas-plain"),
                RoadmapSkillDTO("PyTorch", "مدل‌های عمیق", "devicon-pytorch-original"),
                RoadmapSkillDTO("Docker", "استقرار مدل", "devicon-docker-plain"),
            ),
            projects=(
                RoadmapProjectDTO("تحلیل داده فروش", "پاک‌سازی، نمودار و گزارش قابل ارائه."),
                RoadmapProjectDTO("مدل پیش‌بینی", "train/test، معیارها و بهبود مدل."),
                RoadmapProjectDTO("چت‌بات دانش‌محور", "اتصال LLM، جستجوی متن و پاسخ‌گویی."),
            ),
        )

    @staticmethod
    def freelancer() -> CourseRoadmapDTO:
        return CourseRoadmapDTO(
            slug="freelancer",
            title="Freelancer",
            category=CourseRoadmapCategoryVO.FREELANCER.value,
            category_label=CourseRoadmapCategoryLabelVO.FREELANCER.value,
            description="مسیر ورود به فریلنسری؛ از انتخاب مهارت تا نمونه‌کار، قیمت‌گذاری، قرارداد و جذب مشتری.",
            level="همه سطوح",
            duration_weeks=6,
            icon_class="devicon-github-original",
            related_course_search_terms=("freelancer", "portfolio", "wordpress", "frontend"),
            steps=(
                RoadmapStepDTO(1, "انتخاب مسیر", "انتخاب تخصص، تحلیل بازار و تعریف خدمات قابل فروش.", "۱ هفته", ("Niche", "Market", "Service")),
                RoadmapStepDTO(2, "نمونه‌کار", "ساخت portfolio، case study و GitHub/LinkedIn حرفه‌ای.", "۲ هفته", ("Portfolio", "Case Study", "Profile")),
                RoadmapStepDTO(3, "فروش و مذاکره", "نوشتن پیشنهاد، قیمت‌گذاری، قرارداد و مدیریت انتظار مشتری.", "۲ هفته", ("Proposal", "Pricing", "Contract")),
                RoadmapStepDTO(4, "تحویل و رشد", "تحویل استاندارد، پشتیبانی، دریافت رضایت و جذب پروژه بعدی.", "۱ هفته", ("Delivery", "Support", "Growth")),
            ),
            skills=(
                RoadmapSkillDTO("Portfolio", "نمایش توانایی با پروژه واقعی", "devicon-github-original"),
                RoadmapSkillDTO("Communication", "مذاکره و ارتباط حرفه‌ای", "devicon-slack-plain"),
                RoadmapSkillDTO("Planning", "مدیریت زمان و تحویل", "devicon-trello-plain"),
                RoadmapSkillDTO("Delivery", "مستندسازی و پشتیبانی", "devicon-markdown-original"),
            ),
            projects=(
                RoadmapProjectDTO("پروفایل حرفه‌ای", "صفحه معرفی، خدمات، نمونه‌کار و فرم تماس."),
                RoadmapProjectDTO("پکیج خدمات", "تعریف چند سطح قیمت و خروجی قابل تحویل."),
                RoadmapProjectDTO("پروژه واقعی کوچک", "یک سایت یا داشبورد قابل ارائه به مشتری."),
            ),
        )
