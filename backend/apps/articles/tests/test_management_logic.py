from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from backend.apps.articles.dtos import ArticleAdminFilterDTO, ArticleCreateDTO
from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.articles.logic import ArticleManagementLogic


class ArticleManagementLogicTests(SimpleTestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.logic = ArticleManagementLogic(repository=self.repository)
        self.actor = MagicMock()


    def test_admin_filter_discards_invalid_category_uuid(self):
        dto = ArticleAdminFilterDTO.from_mapping({"category_id": "not-a-uuid"})

        self.assertEqual(dto.category_id, "")

    def test_create_normalizes_values_before_repository_call(self):
        self.repository.create_article.return_value = MagicMock()

        self.logic.create_article(
            actor=self.actor,
            dto=ArticleCreateDTO(
                title="  معماری تمیز  ",
                slug="  معماری تمیز  ",
                excerpt="  خلاصه  ",
                content="  محتوای کامل  ",
                article_type=ArticleTypeEnum.BLOG.value,
                status=ArticleStatusEnum.DRAFT.value,
                tag_ids=["tag-1", "tag-2"],
            ),
        )

        called_dto = self.repository.create_article.call_args.kwargs["dto"]
        self.assertEqual(called_dto.title, "معماری تمیز")
        self.assertEqual(called_dto.slug, "معماری-تمیز")
        self.assertEqual(called_dto.excerpt, "خلاصه")
        self.assertEqual(called_dto.content, "محتوای کامل")
        self.assertEqual(called_dto.tag_ids, ("tag-1", "tag-2"))

    def test_create_rejects_empty_required_fields(self):
        with self.assertRaises(ValidationError) as context:
            self.logic.create_article(
                actor=self.actor,
                dto=ArticleCreateDTO(
                    title=" ",
                    content=" ",
                    article_type=ArticleTypeEnum.BLOG.value,
                    status=ArticleStatusEnum.DRAFT.value,
                ),
            )

        self.assertIn("title", context.exception.message_dict)
        self.assertIn("content", context.exception.message_dict)
        self.repository.create_article.assert_not_called()

    def test_update_text_field_preserves_other_article_values(self):
        article = MagicMock(
            id="article-id",
            title="Old title",
            excerpt="Old excerpt",
            content="Old content",
            article_type=ArticleTypeEnum.NEWS.value,
            status=ArticleStatusEnum.PUBLISHED.value,
            slug="old-title",
            category_id=None,
            is_featured=False,
            published_at=None,
            source_name="",
            source_url="",
            meta_title="",
            meta_description="",
        )
        self.repository.get_admin_article.return_value = article
        self.repository.list_admin_article_tag_ids.return_value = ()
        self.repository.update_article.return_value = article

        self.logic.update_text_field(
            actor=self.actor,
            article_id=article.id,
            field="title",
            value="New title",
        )

        called_dto = self.repository.update_article.call_args.kwargs["dto"]
        self.assertEqual(called_dto.title, "New title")
        self.assertEqual(called_dto.content, "Old content")
        self.assertEqual(called_dto.article_type, ArticleTypeEnum.NEWS.value)

    def test_update_text_field_rejects_unknown_field(self):
        with self.assertRaises(ValidationError):
            self.logic.update_text_field(
                actor=self.actor,
                article_id="article-id",
                field="author_id",
                value="user-id",
            )

        self.repository.get_admin_article.assert_not_called()
        self.repository.update_article.assert_not_called()
