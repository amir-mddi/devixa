# Generated manually for the articles domain app.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ArticleCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("title", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=150, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles_articlecategory_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles_articlecategory_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Article category",
                "verbose_name_plural": "Article categories",
                "ordering": ["position", "title"],
            },
        ),
        migrations.CreateModel(
            name="ArticleTag",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("title", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=100, unique=True)),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles_articletag_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles_articletag_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Article tag",
                "verbose_name_plural": "Article tags",
                "ordering": ["title"],
            },
        ),
        migrations.CreateModel(
            name="Article",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(blank=True, default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("article_type", models.CharField(choices=[("blog", "وبلاگ"), ("news", "اخبار")], db_index=True, default="blog", max_length=20)),
                ("status", models.CharField(choices=[("draft", "پیش‌نویس"), ("published", "منتشرشده"), ("archived", "بایگانی‌شده")], db_index=True, default="draft", max_length=20)),
                ("title", models.CharField(max_length=220)),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=250, unique=True)),
                ("excerpt", models.CharField(blank=True, default="", max_length=420)),
                ("content", models.TextField()),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="articles/covers/%Y/%m/")),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("published_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("view_count", models.PositiveBigIntegerField(default=0, editable=False)),
                ("source_name", models.CharField(blank=True, default="", max_length=150)),
                ("source_url", models.URLField(blank=True, default="")),
                ("meta_title", models.CharField(blank=True, default="", max_length=220)),
                ("meta_description", models.CharField(blank=True, default="", max_length=320)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authored_articles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles",
                        to="articles.articlecategory",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(blank=True, related_name="articles", to="articles.articletag"),
                ),
                (
                    "user_created_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles_article_user_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user_updated_object",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="articles_article_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Article",
                "verbose_name_plural": "Articles",
                "ordering": ["-published_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="articlecategory",
            index=models.Index(fields=["is_active", "is_deleted", "position"], name="article_category_public_idx"),
        ),
        migrations.AddIndex(
            model_name="article",
            index=models.Index(fields=["status", "article_type", "is_active", "is_deleted", "published_at"], name="article_public_list_idx"),
        ),
        migrations.AddIndex(
            model_name="article",
            index=models.Index(fields=["is_featured", "status", "published_at"], name="article_featured_idx"),
        ),
        migrations.AddIndex(
            model_name="article",
            index=models.Index(fields=["slug"], name="article_slug_idx"),
        ),
        migrations.AddConstraint(
            model_name="article",
            constraint=models.CheckConstraint(condition=models.Q(("view_count__gte", 0)), name="article_view_count_gte_zero"),
        ),
    ]
