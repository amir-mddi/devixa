from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from backend.apps.accounts.models import Role
from backend.apps.billing.enums import CurrencyEnum
from backend.apps.common.project_config import get_project_name, get_project_slug
from backend.apps.core_models.vo.common_vo import UserRoleVO
from backend.apps.courses.enums import CourseLevelEnum, CourseStatusEnum
from backend.apps.courses.models import Course, CourseCategory, CourseLesson


@dataclass(frozen=True)
class DemoLessonSeedDTO:
    title: str
    description: str
    duration_minutes: int
    is_preview: bool = False


@dataclass(frozen=True)
class DemoCourseSeedDTO:
    category_slug: str
    title: str
    slug: str
    short_description: str
    description: str
    price: Decimal
    level: str
    duration_minutes: int
    is_featured: bool
    lessons: Sequence[DemoLessonSeedDTO]


@dataclass(frozen=True)
class DemoCategorySeedDTO:
    title: str
    slug: str
    description: str
    position: int


class DemoSeedVO:
    COMMAND_HELP = "Seed demo categories, courses, and lessons for development."
    ADMIN_ROLE_NAME = "مدیر سیستم"
    CREATED_MESSAGE_TEMPLATE = "{project_name} demo courses seeded successfully."
    CATEGORY_DESCRIPTION_SUFFIX = "مسیر آموزشی پروژه محور"


class Command(BaseCommand):
    help = DemoSeedVO.COMMAND_HELP

    def handle(self, *args, **options):
        if getattr(settings, "IS_PROD", False):
            raise CommandError("Demo course seeding is disabled in production.")
        instructor = self._get_or_create_instructor()
        categories = self._seed_categories()
        self._seed_courses(instructor=instructor, categories=categories)
        self.stdout.write(self.style.SUCCESS(DemoSeedVO.CREATED_MESSAGE_TEMPLATE.format(project_name=get_project_name())))

    @staticmethod
    def _get_or_create_instructor():
        role, _ = Role.objects.get_or_create(
            symbol=UserRoleVO.ADMIN,
            defaults={"name": DemoSeedVO.ADMIN_ROLE_NAME},
        )
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=os.getenv("DEMO_ADMIN_USERNAME", f"{get_project_slug()}_admin"),
            defaults={
                "email": os.getenv("DEMO_ADMIN_EMAIL", f"{get_project_slug()}_admin@example.com"),
                "role": role,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if created:
            password = os.getenv("DEMO_ADMIN_PASSWORD", "")
            if not password:
                user.delete(soft=False)
                raise CommandError("DEMO_ADMIN_PASSWORD must be configured for demo seeding.")
            try:
                validate_password(password, user=user)
            except ValidationError as exc:
                user.delete(soft=False)
                raise CommandError("DEMO_ADMIN_PASSWORD is not strong enough.") from exc
            user.set_password(password)
            user.save(update_fields=["password", "updated_at"])
        return user

    @staticmethod
    def _seed_categories() -> dict[str, CourseCategory]:
        categories = {}
        for seed in Command._category_seeds():
            category, _ = CourseCategory.objects.update_or_create(
                slug=seed.slug,
                defaults={
                    "title": seed.title,
                    "description": seed.description,
                    "position": seed.position,
                    "is_active": True,
                    "is_deleted": False,
                },
            )
            categories[seed.slug] = category
        return categories

    @staticmethod
    def _seed_courses(*, instructor, categories: dict[str, CourseCategory]) -> None:
        for seed in Command._course_seeds():
            course, _ = Course.objects.update_or_create(
                slug=seed.slug,
                defaults={
                    "category": categories[seed.category_slug],
                    "instructor": instructor,
                    "title": seed.title,
                    "short_description": seed.short_description,
                    "description": seed.description,
                    "price": seed.price,
                    "currency": CurrencyEnum.IRR.value,
                    "level": seed.level,
                    "status": CourseStatusEnum.PUBLISHED.value,
                    "duration_minutes": seed.duration_minutes,
                    "is_featured": seed.is_featured,
                    "published_at": now(),
                    "is_active": True,
                    "is_deleted": False,
                    "user_created_object": instructor,
                    "user_updated_object": instructor,
                },
            )
            Command._seed_lessons(course=course, instructor=instructor, lesson_seeds=seed.lessons)

    @staticmethod
    def _seed_lessons(*, course: Course, instructor, lesson_seeds: Sequence[DemoLessonSeedDTO]) -> None:
        for position, seed in enumerate(lesson_seeds, start=1):
            CourseLesson.objects.update_or_create(
                course=course,
                position=position,
                defaults={
                    "title": seed.title,
                    "slug": f"lesson-{position}",
                    "description": seed.description,
                    "duration_minutes": seed.duration_minutes,
                    "is_preview": seed.is_preview,
                    "is_active": True,
                    "is_deleted": False,
                    "user_created_object": instructor,
                    "user_updated_object": instructor,
                },
            )

    @staticmethod
    def _category_seeds() -> tuple[DemoCategorySeedDTO, ...]:
        return (
            DemoCategorySeedDTO("فرانت‌اند", "frontend", DemoSeedVO.CATEGORY_DESCRIPTION_SUFFIX, 1),
            DemoCategorySeedDTO("بک‌اند", "backend", DemoSeedVO.CATEGORY_DESCRIPTION_SUFFIX, 2),
            DemoCategorySeedDTO("فول‌استک", "fullstack", DemoSeedVO.CATEGORY_DESCRIPTION_SUFFIX, 3),
            DemoCategorySeedDTO("فریلنسری", "freelancer", DemoSeedVO.CATEGORY_DESCRIPTION_SUFFIX, 4),
        )

    @staticmethod
    def _course_seeds() -> tuple[DemoCourseSeedDTO, ...]:
        return (
            DemoCourseSeedDTO(
                category_slug="backend",
                title="Django Clean Architecture",
                slug="django-clean-architecture",
                short_description="ساخت API و template layer تمیز با DTO، VO، repository و adapter.",
                description="در این دوره یک پروژه واقعی Django را با معماری تمیز، جداسازی لایه‌ها، اعتبارسنجی، احراز هویت و صفحات template کامل می‌سازید.",
                price=Decimal("2200000"),
                level=CourseLevelEnum.INTERMEDIATE.value,
                duration_minutes=1080,
                is_featured=True,
                lessons=(
                    DemoLessonSeedDTO("ساختار پروژه و لایه‌ها", "چیدمان apps، web layer، DTO، VO و repository.", 90, True),
                    DemoLessonSeedDTO("احراز هویت و session", "پیاده‌سازی login/register بدون تکرار منطق API.", 120, True),
                    DemoLessonSeedDTO("Course catalog", "لیست، فیلتر، جستجو و جزئیات دوره‌ها.", 150),
                    DemoLessonSeedDTO("Best practices", "کاهش coupling، تست‌پذیری و آماده‌سازی برای production.", 180),
                ),
            ),
            DemoCourseSeedDTO(
                category_slug="frontend",
                title="React Project Mastery",
                slug="react-project-mastery",
                short_description="ساخت رابط کاربری حرفه‌ای، فیلتر دوره‌ها و اتصال به API.",
                description="این دوره برای توسعه‌دهندگانی است که می‌خواهند React را با پروژه‌های واقعی، کامپوننت تمیز و تجربه کاربری حرفه‌ای یاد بگیرند.",
                price=Decimal("1900000"),
                level=CourseLevelEnum.INTERMEDIATE.value,
                duration_minutes=960,
                is_featured=True,
                lessons=(
                    DemoLessonSeedDTO("Component Design", "طراحی کامپوننت‌های قابل استفاده مجدد.", 100, True),
                    DemoLessonSeedDTO("State and Forms", "مدیریت state و فرم‌های پیچیده.", 120),
                    DemoLessonSeedDTO("API Integration", "اتصال به API و مدیریت loading/error.", 160),
                ),
            ),
            DemoCourseSeedDTO(
                category_slug="fullstack",
                title="Fullstack Course Platform",
                slug="fullstack-course-platform",
                short_description="ساخت پلتفرم فروش دوره از UI تا API و پرداخت.",
                description="در این مسیر یک پلتفرم کامل آموزشی شامل دوره‌ها، ثبت‌نام، پرداخت، پنل کاربر و پنل ادمین ساخته می‌شود.",
                price=Decimal("3500000"),
                level=CourseLevelEnum.ADVANCED.value,
                duration_minutes=1440,
                is_featured=True,
                lessons=(
                    DemoLessonSeedDTO("Product Architecture", "طراحی دامنه و مرزبندی frontend/backend.", 120, True),
                    DemoLessonSeedDTO("Course and Billing", "دوره‌ها، سفارش و جریان پرداخت.", 180),
                    DemoLessonSeedDTO("Deployment", "استقرار، static files و مانیتورینگ.", 180),
                ),
            ),
            DemoCourseSeedDTO(
                category_slug="freelancer",
                title="WordPress Freelancer Road",
                slug="wordpress-freelancer-road",
                short_description="طراحی سایت، تحویل پروژه و جذب مشتری برای فریلنسری.",
                description="این دوره مسیر سریع ورود به پروژه‌های طراحی سایت و فریلنسری را با تمرکز بر نمونه‌کار و تحویل حرفه‌ای پوشش می‌دهد.",
                price=Decimal("1200000"),
                level=CourseLevelEnum.BEGINNER.value,
                duration_minutes=720,
                is_featured=False,
                lessons=(
                    DemoLessonSeedDTO("راه‌اندازی سایت", "دامنه، هاست و نصب وردپرس.", 80, True),
                    DemoLessonSeedDTO("طراحی صفحات", "ساخت صفحات فروش و معرفی خدمات.", 120),
                    DemoLessonSeedDTO("تحویل به مشتری", "چک‌لیست تحویل، آموزش و پشتیبانی.", 100),
                ),
            ),
        )
