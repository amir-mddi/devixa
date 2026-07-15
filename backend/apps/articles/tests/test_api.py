from django.urls import reverse
from rest_framework.test import APITestCase

from backend.apps.articles.enums import ArticleStatusEnum
from backend.tests.factories import ArticleFactory


class PublicArticleAPITests(APITestCase):
    def test_list_returns_published_articles_only(self):
        published = ArticleFactory.create(title="Public Article")
        ArticleFactory.create(title="Draft Article", status=ArticleStatusEnum.DRAFT.value)

        response = self.client.get(reverse("articles_api:article-list"))

        self.assertEqual(response.status_code, 200)
        response_text = str(response.data)
        self.assertIn(published.title, response_text)
        self.assertNotIn("Draft Article", response_text)

    def test_detail_supports_slug(self):
        article = ArticleFactory.create(slug="api-article")

        response = self.client.get(
            reverse(
                "articles_api:article-detail",
                kwargs={"article_id_or_slug": article.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["slug"], article.slug)
