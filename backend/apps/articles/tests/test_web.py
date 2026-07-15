from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.tests.factories import ArticleCategoryFactory, ArticleFactory, ProjectConfigFactory


class ArticleWebPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ProjectConfigFactory.create()
        cls.category = ArticleCategoryFactory.create(title="Django", slug="django")
        cls.blog = ArticleFactory.create(
            title="Clean Django Architecture",
            slug="clean-django-architecture",
            category=cls.category,
            article_type=ArticleTypeEnum.BLOG.value,
            published_at=now(),
        )
        cls.news = ArticleFactory.create(
            title="Django Release News",
            slug="django-release-news",
            category=cls.category,
            article_type=ArticleTypeEnum.NEWS.value,
            published_at=now(),
        )
        ArticleFactory.create(
            title="Hidden Draft",
            slug="hidden-draft",
            status=ArticleStatusEnum.DRAFT.value,
        )

    def test_article_list_shows_only_published_articles(self):
        response = self.client.get(reverse("articles_web:article_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.blog.title)
        self.assertContains(response, self.news.title)
        self.assertNotContains(response, "Hidden Draft")

    def test_blog_page_filters_news(self):
        response = self.client.get(reverse("articles_web:blog_list"))

        self.assertContains(response, self.blog.title)
        self.assertNotContains(response, self.news.title)

    def test_news_page_filters_blog(self):
        response = self.client.get(reverse("articles_web:news_list"))

        self.assertContains(response, self.news.title)
        self.assertNotContains(response, self.blog.title)

    def test_detail_page_increments_view_count(self):
        response = self.client.get(
            reverse("articles_web:article_detail", kwargs={"slug": self.blog.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.view_count, 1)

    def test_draft_detail_returns_404(self):
        response = self.client.get(
            reverse("articles_web:article_detail", kwargs={"slug": "hidden-draft"})
        )

        self.assertEqual(response.status_code, 404)
