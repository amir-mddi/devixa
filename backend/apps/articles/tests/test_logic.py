from unittest.mock import MagicMock

from django.test import SimpleTestCase

from backend.apps.articles.dtos import ArticleCatalogFilterDTO
from backend.apps.articles.logic import ArticleLogic


class ArticleCatalogFilterDTOTests(SimpleTestCase):
    def test_invalid_page_is_normalized(self):
        dto = ArticleCatalogFilterDTO.from_mapping(
            {"page": "bad", "search": "  django  "}
        )

        self.assertEqual(dto.page, 1)
        self.assertEqual(dto.search, "django")


class ArticleLogicTests(SimpleTestCase):
    def test_detail_increments_view_count_after_loading_article(self):
        repository = MagicMock()
        article = MagicMock(id="article-id", view_count=4)
        repository.get_public_article.return_value = article
        repository.list_related_articles.return_value = ()
        logic = ArticleLogic(repository=repository)

        detail = logic.get_detail("article-slug")

        repository.increment_view_count.assert_called_once_with("article-id")
        self.assertEqual(detail.article.view_count, 5)
