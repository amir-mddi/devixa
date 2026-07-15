from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from django.core.paginator import Paginator
from django.test import SimpleTestCase

from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.telegram_bot.enums.article_bot_enums import ArticleBotStepEnum
from backend.apps.telegram_bot.logic.article_bot_logic import ArticleBotLogic
from backend.apps.telegram_bot.vo.article_bot_vo import ArticleBotCallbackVO


class InMemoryArticleStateRepository:
    def __init__(self):
        self.values = {}

    def get(self, chat_id):
        return self.values.get(chat_id, {})

    def set(self, chat_id, state):
        self.values[chat_id] = state

    def clear(self, chat_id):
        self.values.pop(chat_id, None)


class ArticleBotLogicTests(SimpleTestCase):
    def setUp(self):
        self.public_logic = MagicMock()
        self.management_logic = MagicMock()
        self.state_repository = InMemoryArticleStateRepository()
        self.logic = ArticleBotLogic(
            cache_prefix="telegram",
            public_logic=self.public_logic,
            management_logic=self.management_logic,
            state_repository=self.state_repository,
        )
        self.admin = SimpleNamespace(id=uuid4())

    @staticmethod
    def article(**overrides):
        values = {
            "id": uuid4(),
            "title": "خبر تست",
            "slug": "test-news",
            "excerpt": "خلاصه خبر",
            "content": "محتوای خبر",
            "article_type": ArticleTypeEnum.NEWS.value,
            "status": ArticleStatusEnum.DRAFT.value,
            "is_featured": False,
            "published_at": None,
            "view_count": 0,
            "estimated_reading_minutes": 1,
            "source_name": "",
            "source_url": "",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_non_article_callback_is_not_consumed(self):
        result = self.logic.handle_callback(
            chat_id=10,
            language="fa",
            data="course:list:1",
            admin_user=None,
        )

        self.assertFalse(result.handled)

    def test_admin_callbacks_are_rejected_for_normal_users(self):
        result = self.logic.handle_callback(
            chat_id=10,
            language="fa",
            data=ArticleBotCallbackVO.admin_list(1),
            admin_user=None,
        )

        self.assertTrue(result.handled)
        self.assertIn("فقط برای مدیران", result.screen.text)
        self.management_logic.list_articles.assert_not_called()

    def test_public_list_uses_public_article_usecase(self):
        article = self.article(status=ArticleStatusEnum.PUBLISHED.value)
        self.public_logic.paginate_public_for_bot.return_value = Paginator(
            [article],
            5,
        ).get_page(1)

        screen = self.logic.public_list_screen(
            language="fa",
            article_type=ArticleTypeEnum.NEWS.value,
            page=1,
        )

        self.assertIn(article.title, screen.text)
        self.public_logic.paginate_public_for_bot.assert_called_once_with(
            article_type=ArticleTypeEnum.NEWS.value,
            page=1,
            page_size=5,
        )

    def test_admin_can_complete_create_article_state_flow(self):
        created = self.article(status=ArticleStatusEnum.PUBLISHED.value)
        self.management_logic.create_article.return_value = created
        self.management_logic.get_article.return_value = created

        self.logic.handle_callback(
            chat_id=20,
            language="fa",
            data=ArticleBotCallbackVO.CREATE,
            admin_user=self.admin,
        )
        self.logic.handle_text(
            chat_id=20,
            language="fa",
            text="عنوان جدید",
            admin_user=self.admin,
        )
        self.logic.handle_text(
            chat_id=20,
            language="fa",
            text="خلاصه جدید",
            admin_user=self.admin,
        )
        content_result = self.logic.handle_text(
            chat_id=20,
            language="fa",
            text="محتوای کامل مطلب جدید",
            admin_user=self.admin,
        )

        self.assertEqual(
            self.state_repository.get(20)["step"],
            ArticleBotStepEnum.CREATE_TYPE.value,
        )
        self.assertIn("نوع مطلب", content_result.screen.text)

        self.logic.handle_callback(
            chat_id=20,
            language="fa",
            data=ArticleBotCallbackVO.create_type(ArticleTypeEnum.BLOG.value),
            admin_user=self.admin,
        )
        result = self.logic.handle_callback(
            chat_id=20,
            language="fa",
            data=ArticleBotCallbackVO.create_status(ArticleStatusEnum.PUBLISHED.value),
            admin_user=self.admin,
        )

        dto = self.management_logic.create_article.call_args.kwargs["dto"]
        self.assertEqual(dto.title, "عنوان جدید")
        self.assertEqual(dto.excerpt, "خلاصه جدید")
        self.assertEqual(dto.content, "محتوای کامل مطلب جدید")
        self.assertEqual(dto.article_type, ArticleTypeEnum.BLOG.value)
        self.assertEqual(dto.status, ArticleStatusEnum.PUBLISHED.value)
        self.assertEqual(self.state_repository.get(20), {})
        self.assertIn("با موفقیت ایجاد شد", result.screen.text)


    def test_admin_can_change_article_type(self):
        article = self.article(article_type=ArticleTypeEnum.BLOG.value)
        self.management_logic.update_type.return_value = article
        self.management_logic.get_article.return_value = article

        result = self.logic.handle_callback(
            chat_id=30,
            language="fa",
            data=ArticleBotCallbackVO.edit_type(
                article.id,
                ArticleTypeEnum.BLOG.value,
            ),
            admin_user=self.admin,
        )

        self.management_logic.update_type.assert_called_once_with(
            actor=self.admin,
            article_id=str(article.id),
            article_type=ArticleTypeEnum.BLOG.value,
        )
        self.assertIn("با موفقیت به‌روزرسانی شد", result.screen.text)

    def test_callback_payloads_fit_telegram_limit(self):
        article_id = uuid4()
        callbacks = (
            ArticleBotCallbackVO.detail(article_id),
            ArticleBotCallbackVO.edit(article_id),
            ArticleBotCallbackVO.edit_field(article_id, "meta_description"),
            ArticleBotCallbackVO.edit_type(article_id, ArticleTypeEnum.NEWS.value),
            ArticleBotCallbackVO.edit_status(article_id, ArticleStatusEnum.PUBLISHED.value),
            ArticleBotCallbackVO.toggle_featured(article_id),
            ArticleBotCallbackVO.delete(article_id),
            ArticleBotCallbackVO.delete_confirm(article_id),
        )

        for callback in callbacks:
            with self.subTest(callback=callback):
                self.assertLessEqual(len(callback.encode("utf-8")), 64)
