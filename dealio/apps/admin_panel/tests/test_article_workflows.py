from django.test import TestCase
from django.urls import reverse

from dealio.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from dealio.apps.articles.models import Article
from dealio.tests.factories import (
    ArticleCategoryFactory,
    ArticleTagFactory,
    RoleFactory,
    UserFactory,
)


class AdminArticleWorkflowTests(TestCase):
    def setUp(self):
        admin_role = RoleFactory.create(name="ادمین محتوا", symbol="admin")
        self.admin = UserFactory.create(role=admin_role)
        self.category = ArticleCategoryFactory.create(title="فناوری")
        self.tag = ArticleTagFactory.create(title="جنگو")
        self.client.force_login(self.admin)

    def article_payload(self, **overrides):
        payload = {
            "article_type": ArticleTypeEnum.NEWS.value,
            "status": ArticleStatusEnum.PUBLISHED.value,
            "title": "خبر انتشار نسخه جدید",
            "slug": "",
            "excerpt": "خلاصه خبر",
            "content": "محتوای کامل خبر برای انتشار در سایت و ربات.",
            "category_id": str(self.category.id),
            "tag_ids": [str(self.tag.id)],
            "is_featured": "on",
            "published_at": "",
            "source_name": "Devixa",
            "source_url": "https://example.com/source",
            "meta_title": "عنوان سئو خبر",
            "meta_description": "توضیحات سئو خبر",
        }
        payload.update(overrides)
        return payload

    def test_admin_can_create_article(self):
        response = self.client.post(
            reverse("admin_panel:article_create"),
            self.article_payload(),
        )

        self.assertRedirects(response, reverse("admin_panel:articles"))
        article = Article.objects.get(title="خبر انتشار نسخه جدید")
        self.assertEqual(article.author, self.admin)
        self.assertEqual(article.article_type, ArticleTypeEnum.NEWS.value)
        self.assertEqual(article.status, ArticleStatusEnum.PUBLISHED.value)
        self.assertEqual(article.category, self.category)
        self.assertTrue(article.tags.filter(id=self.tag.id).exists())
        self.assertTrue(article.is_featured)
        self.assertIsNotNone(article.published_at)

    def test_admin_can_edit_article_without_replacing_cover(self):
        article = Article.objects.create(
            author=self.admin,
            title="عنوان قبلی",
            content="محتوای قبلی",
            article_type=ArticleTypeEnum.BLOG.value,
            status=ArticleStatusEnum.DRAFT.value,
        )

        response = self.client.post(
            reverse("admin_panel:article_edit", kwargs={"article_id": article.id}),
            self.article_payload(
                title="عنوان ویرایش‌شده",
                status=ArticleStatusEnum.ARCHIVED.value,
                is_featured="",
            ),
        )

        self.assertRedirects(response, reverse("admin_panel:articles"))
        article.refresh_from_db()
        self.assertEqual(article.title, "عنوان ویرایش‌شده")
        self.assertEqual(article.status, ArticleStatusEnum.ARCHIVED.value)
        self.assertFalse(article.is_featured)
        self.assertEqual(article.user_updated_object, self.admin)

    def test_admin_delete_uses_soft_delete(self):
        article = Article.objects.create(
            author=self.admin,
            title="مطلب قابل حذف",
            content="محتوا",
            article_type=ArticleTypeEnum.BLOG.value,
            status=ArticleStatusEnum.DRAFT.value,
        )

        response = self.client.post(
            reverse("admin_panel:article_delete", kwargs={"article_id": article.id})
        )

        self.assertRedirects(response, reverse("admin_panel:articles"))
        article.refresh_from_db()
        self.assertTrue(article.is_deleted)
        self.assertFalse(article.is_active)
        self.assertEqual(article.user_updated_object, self.admin)

    def test_article_list_supports_type_status_and_category_filters(self):
        Article.objects.create(
            author=self.admin,
            category=self.category,
            title="خبر فیلترشده",
            content="محتوا",
            article_type=ArticleTypeEnum.NEWS.value,
            status=ArticleStatusEnum.DRAFT.value,
        )
        Article.objects.create(
            author=self.admin,
            title="وبلاگ نامرتبط",
            content="محتوا",
            article_type=ArticleTypeEnum.BLOG.value,
            status=ArticleStatusEnum.PUBLISHED.value,
        )

        response = self.client.get(
            reverse("admin_panel:articles"),
            {
                "article_type": ArticleTypeEnum.NEWS.value,
                "status": ArticleStatusEnum.DRAFT.value,
                "category_id": str(self.category.id),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "خبر فیلترشده")
        self.assertNotContains(response, "وبلاگ نامرتبط")
