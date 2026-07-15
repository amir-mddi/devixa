from django.test import TestCase

from backend.apps.articles.enums import ArticleStatusEnum
from backend.apps.articles.models import ArticleCategory
from backend.tests.factories import ArticleFactory


class ArticleModelTests(TestCase):
    def test_article_generates_unicode_slug_and_publish_date(self):
        article = ArticleFactory.create(
            title="راهنمای معماری تمیز",
            slug="",
            status=ArticleStatusEnum.PUBLISHED.value,
            published_at=None,
        )

        self.assertIn("راهنمای-معماری-تمیز", article.slug)
        self.assertIsNotNone(article.published_at)
        self.assertTrue(article.is_published)

    def test_category_generates_stable_slug(self):
        category = ArticleCategory.objects.create(title="اخبار فناوری", slug="")

        self.assertIn("اخبار-فناوری", category.slug)

    def test_reading_time_is_at_least_one_minute(self):
        article = ArticleFactory.create(content="متن کوتاه")

        self.assertEqual(article.estimated_reading_minutes, 1)

    def test_draft_article_is_not_public(self):
        article = ArticleFactory.create(status=ArticleStatusEnum.DRAFT.value)

        self.assertFalse(article.is_published)
