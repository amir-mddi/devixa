from __future__ import annotations

import html
from typing import Any

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from rest_framework.exceptions import APIException

from backend.apps.articles.dtos import ArticleCreateDTO
from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.articles.logic import ArticleLogic, ArticleManagementLogic
from backend.apps.telegram_bot.dtos.article_bot_dtos import (
    ArticleBotButtonDTO,
    ArticleBotHandleResultDTO,
    ArticleBotScreenDTO,
)
from backend.apps.telegram_bot.enums.article_bot_enums import (
    ArticleBotFieldEnum,
    ArticleBotFlowEnum,
    ArticleBotStepEnum,
)
from backend.apps.telegram_bot.repositories.article_bot_state_repository import (
    ArticleBotStateRepository,
)
from backend.apps.telegram_bot.vo.article_bot_vo import (
    ArticleBotButtonTextVO,
    ArticleBotCallbackVO,
    ArticleBotInputVO,
    ArticleBotLabelVO,
    ArticleBotTextVO,
)


class ArticleBotLogic:
    PUBLIC_PAGE_SIZE = 5
    ADMIN_PAGE_SIZE = 5

    def __init__(
        self,
        *,
        cache_prefix: str,
        public_logic: ArticleLogic | None = None,
        management_logic: ArticleManagementLogic | None = None,
        state_repository: ArticleBotStateRepository | None = None,
    ):
        self.public_logic = public_logic or ArticleLogic()
        self.management_logic = management_logic or ArticleManagementLogic()
        self.state_repository = state_repository or ArticleBotStateRepository(
            cache_prefix=cache_prefix
        )

    def clear_state(self, chat_id: int) -> None:
        self.state_repository.clear(chat_id)

    def menu_screen(self, *, language: str, is_admin: bool) -> ArticleBotScreenDTO:
        rows = [
            (
                self._button(language, "all", ArticleBotCallbackVO.public_list("all", 1)),
                self._button(language, "blog", ArticleBotCallbackVO.public_list("blog", 1)),
            ),
            (self._button(language, "news", ArticleBotCallbackVO.public_list("news", 1)),),
        ]
        if is_admin:
            rows.append(
                (
                    self._button(language, "admin_articles", ArticleBotCallbackVO.admin_list(1)),
                    self._button(language, "new", ArticleBotCallbackVO.CREATE),
                )
            )
        rows.append((self._button(language, "main_menu", ArticleBotCallbackVO.MAIN_MENU),))
        return ArticleBotScreenDTO(
            text=ArticleBotTextVO.get(
                language,
                "admin_menu_title" if is_admin else "menu_title",
            ),
            rows=tuple(rows),
        )

    def handle_callback(
        self,
        *,
        chat_id: int,
        language: str,
        data: str,
        admin_user: Any | None,
    ) -> ArticleBotHandleResultDTO:
        if not data.startswith(ArticleBotCallbackVO.PREFIX):
            return ArticleBotHandleResultDTO(handled=False)

        try:
            screen = self._dispatch_callback(
                chat_id=chat_id,
                language=language,
                data=data,
                admin_user=admin_user,
            )
        except (ValidationError, APIException, ValueError) as exc:
            screen = self._error_screen(language, exc)
        return ArticleBotHandleResultDTO(handled=True, screen=screen)

    def handle_text(
        self,
        *,
        chat_id: int,
        language: str,
        text: str,
        admin_user: Any | None,
    ) -> ArticleBotHandleResultDTO:
        state = self.state_repository.get(chat_id)
        if not state:
            return ArticleBotHandleResultDTO(handled=False)
        if admin_user is None:
            self.clear_state(chat_id)
            return ArticleBotHandleResultDTO(
                handled=True,
                screen=self._message_screen(language, "admin_only"),
            )

        try:
            screen = self._consume_state_text(
                chat_id=chat_id,
                language=language,
                text=text.strip(),
                admin_user=admin_user,
                state=state,
            )
        except (ValidationError, APIException, ValueError) as exc:
            screen = self._error_screen(language, exc)
        return ArticleBotHandleResultDTO(handled=True, screen=screen)

    def _dispatch_callback(
        self,
        *,
        chat_id: int,
        language: str,
        data: str,
        admin_user: Any | None,
    ) -> ArticleBotScreenDTO:
        if data == ArticleBotCallbackVO.MENU:
            self.clear_state(chat_id)
            return self.menu_screen(language=language, is_admin=admin_user is not None)
        if data == ArticleBotCallbackVO.CANCEL:
            self.clear_state(chat_id)
            return self.menu_screen(language=language, is_admin=admin_user is not None)

        parts = data.split(":")
        if data.startswith(f"{ArticleBotCallbackVO.PUBLIC_LIST_PREFIX}:") and len(parts) == 4:
            return self.public_list_screen(
                language=language,
                article_type=parts[2],
                page=self._positive_int(parts[3]),
            )
        if data.startswith(f"{ArticleBotCallbackVO.DETAIL_PREFIX}:") and len(parts) == 3:
            return self.detail_screen(language=language, article_id=parts[2], is_admin=admin_user is not None)

        if admin_user is None:
            self.clear_state(chat_id)
            return self._message_screen(language, "admin_only")
        if data.startswith(f"{ArticleBotCallbackVO.ADMIN_LIST_PREFIX}:") and len(parts) == 3:
            return self.admin_list_screen(language=language, page=self._positive_int(parts[2]))
        if data == ArticleBotCallbackVO.CREATE:
            return self._start_create(chat_id=chat_id, language=language)
        if data.startswith(f"{ArticleBotCallbackVO.CREATE_TYPE_PREFIX}:") and len(parts) == 3:
            return self._select_create_type(chat_id=chat_id, language=language, article_type=parts[2])
        if data.startswith(f"{ArticleBotCallbackVO.CREATE_STATUS_PREFIX}:") and len(parts) == 3:
            return self._finish_create(
                chat_id=chat_id,
                language=language,
                admin_user=admin_user,
                status=parts[2],
            )
        if data.startswith(f"{ArticleBotCallbackVO.EDIT_PREFIX}:") and len(parts) == 3:
            return self.admin_detail_screen(language=language, article_id=parts[2])
        if data.startswith(f"{ArticleBotCallbackVO.EDIT_FIELD_PREFIX}:") and len(parts) == 4:
            return self._start_edit_field(
                chat_id=chat_id,
                language=language,
                article_id=parts[2],
                field=parts[3],
            )
        if data.startswith(f"{ArticleBotCallbackVO.EDIT_TYPE_PREFIX}:") and len(parts) == 4:
            if parts[3] not in ArticleTypeEnum.values():
                raise ValidationError(ArticleBotTextVO.get(language, "invalid_type"))
            article = self.management_logic.update_type(
                actor=admin_user,
                article_id=parts[2],
                article_type=parts[3],
            )
            return self._success_then_admin_detail(language, "updated", article.id)
        if data.startswith(f"{ArticleBotCallbackVO.EDIT_STATUS_PREFIX}:") and len(parts) == 4:
            if parts[3] not in ArticleStatusEnum.values():
                raise ValidationError(ArticleBotTextVO.get(language, "invalid_status"))
            article = self.management_logic.update_status(
                actor=admin_user,
                article_id=parts[2],
                status=parts[3],
            )
            return self._success_then_admin_detail(language, "updated", article.id)
        if data.startswith(f"{ArticleBotCallbackVO.TOGGLE_FEATURED_PREFIX}:") and len(parts) == 3:
            article = self.management_logic.toggle_featured(
                actor=admin_user,
                article_id=parts[2],
            )
            return self._success_then_admin_detail(language, "featured_updated", article.id)
        if data.startswith(f"{ArticleBotCallbackVO.DELETE_CONFIRM_PREFIX}:") and len(parts) == 3:
            self.management_logic.delete_article(actor=admin_user, article_id=parts[2])
            self.clear_state(chat_id)
            return ArticleBotScreenDTO(
                text=ArticleBotTextVO.get(language, "deleted"),
                rows=(
                    (self._button(language, "admin_articles", ArticleBotCallbackVO.admin_list(1)),),
                    (self._button(language, "main_menu", ArticleBotCallbackVO.MAIN_MENU),),
                ),
            )
        if data.startswith(f"{ArticleBotCallbackVO.DELETE_PREFIX}:") and len(parts) == 3:
            article = self.management_logic.get_article(parts[2])
            return ArticleBotScreenDTO(
                text=ArticleBotTextVO.get(
                    language,
                    "delete_confirm",
                    title=html.escape(article.title),
                ),
                rows=(
                    (self._button(language, "confirm_delete", ArticleBotCallbackVO.delete_confirm(article.id)),),
                    (self._button(language, "back", ArticleBotCallbackVO.edit(article.id)),),
                ),
            )
        return self._message_screen(language, "not_found")

    def public_list_screen(self, *, language: str, article_type: str, page: int) -> ArticleBotScreenDTO:
        article_type = article_type if article_type in {"all", *ArticleTypeEnum.values()} else "all"
        page_obj = self.public_logic.paginate_public_for_bot(
            article_type=article_type,
            page=page,
            page_size=self.PUBLIC_PAGE_SIZE,
        )
        lines = [
            ArticleBotTextVO.get(
                language,
                "list_title",
                label=ArticleBotLabelVO.type_label(language, article_type),
                page=page_obj.number,
                pages=page_obj.paginator.num_pages,
            )
        ]
        rows: list[tuple[ArticleBotButtonDTO, ...]] = []
        if not page_obj.object_list:
            lines.append(f"\n{ArticleBotTextVO.get(language, 'list_empty')}")
        for article in page_obj.object_list:
            lines.append(f"\n\n{self._format_public_row(language, article)}")
            rows.append(
                (
                    ArticleBotButtonDTO(
                        text=Truncator(article.title).chars(35),
                        callback_data=ArticleBotCallbackVO.detail(article.id),
                    ),
                )
            )
        rows.extend(self._pagination_rows(language, page_obj, ArticleBotCallbackVO.PUBLIC_LIST_PREFIX, article_type))
        rows.append((self._button(language, "back", ArticleBotCallbackVO.MENU),))
        return ArticleBotScreenDTO(text="".join(lines), rows=tuple(rows))

    def detail_screen(self, *, language: str, article_id: object, is_admin: bool) -> ArticleBotScreenDTO:
        detail = self.public_logic.get_detail(article_id)
        article = detail.article
        source = ""
        if article.source_name or article.source_url:
            source_value = article.source_name or article.source_url
            source = f"\n🔗 {html.escape(source_value)}"
        text = ArticleBotTextVO.get(
            language,
            "detail",
            icon=self._type_icon(article.article_type),
            title=html.escape(article.title),
            excerpt=html.escape(article.excerpt or "—"),
            content=html.escape(Truncator(strip_tags(article.content or "")).chars(2200)),
            date=self._date(article.published_at),
            minutes=article.estimated_reading_minutes,
            views=article.view_count,
            source=source,
        )
        rows = [(self._button(language, "back", ArticleBotCallbackVO.MENU),)]
        if is_admin:
            rows.insert(0, (self._button(language, "edit", ArticleBotCallbackVO.edit(article.id)),))
        return ArticleBotScreenDTO(text=text, rows=tuple(rows))

    def admin_list_screen(self, *, language: str, page: int) -> ArticleBotScreenDTO:
        page_obj = self.management_logic.paginate_articles(
            page=page,
            page_size=self.ADMIN_PAGE_SIZE,
        )
        lines = [
            ArticleBotTextVO.get(
                language,
                "admin_list_title",
                page=page_obj.number,
                pages=page_obj.paginator.num_pages,
            )
        ]
        rows: list[tuple[ArticleBotButtonDTO, ...]] = []
        if not page_obj.object_list:
            lines.append(f"\n{ArticleBotTextVO.get(language, 'admin_list_empty')}")
        for article in page_obj.object_list:
            lines.append(f"\n\n{self._format_admin_row(language, article)}")
            rows.append(
                (
                    ArticleBotButtonDTO(
                        text=Truncator(article.title).chars(31),
                        callback_data=ArticleBotCallbackVO.edit(article.id),
                    ),
                )
            )
        rows.extend(self._admin_pagination_rows(language, page_obj))
        rows.append((self._button(language, "new", ArticleBotCallbackVO.CREATE),))
        rows.append((self._button(language, "back", ArticleBotCallbackVO.MENU),))
        return ArticleBotScreenDTO(text="".join(lines), rows=tuple(rows))

    def admin_detail_screen(self, *, language: str, article_id: object) -> ArticleBotScreenDTO:
        article = self.management_logic.get_article(article_id)
        text = ArticleBotTextVO.get(
            language,
            "admin_detail",
            title=html.escape(article.title),
            type_label=ArticleBotLabelVO.type_label(language, article.article_type),
            status_label=ArticleBotLabelVO.status_label(language, article.status),
            featured=ArticleBotLabelVO.yes_no(language, article.is_featured),
            date=self._date(article.published_at),
            views=article.view_count,
            slug=html.escape(article.slug),
        )
        field_rows = []
        fields = list(ArticleBotFieldEnum)
        for index in range(0, len(fields), 2):
            field_rows.append(
                tuple(
                    self._button(
                        language,
                        field.value,
                        ArticleBotCallbackVO.edit_field(article.id, field.value),
                    )
                    for field in fields[index : index + 2]
                )
            )
        rows = [
            *field_rows,
            (
                self._button(
                    language,
                    "set_blog",
                    ArticleBotCallbackVO.edit_type(
                        article.id,
                        ArticleTypeEnum.BLOG.value,
                    ),
                ),
                self._button(
                    language,
                    "set_news",
                    ArticleBotCallbackVO.edit_type(
                        article.id,
                        ArticleTypeEnum.NEWS.value,
                    ),
                ),
            ),
            (
                self._button(language, "draft", ArticleBotCallbackVO.edit_status(article.id, ArticleStatusEnum.DRAFT.value)),
                self._button(language, "published", ArticleBotCallbackVO.edit_status(article.id, ArticleStatusEnum.PUBLISHED.value)),
            ),
            (
                self._button(language, "archived", ArticleBotCallbackVO.edit_status(article.id, ArticleStatusEnum.ARCHIVED.value)),
                self._button(language, "featured", ArticleBotCallbackVO.toggle_featured(article.id)),
            ),
            (self._button(language, "delete", ArticleBotCallbackVO.delete(article.id)),),
            (self._button(language, "back", ArticleBotCallbackVO.admin_list(1)),),
        ]
        return ArticleBotScreenDTO(text=text, rows=tuple(rows))

    def _start_create(self, *, chat_id: int, language: str) -> ArticleBotScreenDTO:
        self.state_repository.set(
            chat_id,
            {
                "flow": ArticleBotFlowEnum.CREATE.value,
                "step": ArticleBotStepEnum.CREATE_TITLE.value,
                "data": {},
            },
        )
        return self._prompt_screen(language, "create_title_prompt")

    def _select_create_type(self, *, chat_id: int, language: str, article_type: str) -> ArticleBotScreenDTO:
        state = self.state_repository.get(chat_id)
        if state.get("step") != ArticleBotStepEnum.CREATE_TYPE.value:
            self.clear_state(chat_id)
            return self._message_screen(language, "session_expired")
        if article_type not in ArticleTypeEnum.values():
            raise ValidationError(ArticleBotTextVO.get(language, "invalid_type"))
        state["data"]["article_type"] = article_type
        state["step"] = ArticleBotStepEnum.CREATE_STATUS.value
        self.state_repository.set(chat_id, state)
        return ArticleBotScreenDTO(
            text=ArticleBotTextVO.get(language, "create_status_prompt"),
            rows=(
                (
                    self._button(language, "draft", ArticleBotCallbackVO.create_status(ArticleStatusEnum.DRAFT.value)),
                    self._button(language, "published", ArticleBotCallbackVO.create_status(ArticleStatusEnum.PUBLISHED.value)),
                ),
                (self._button(language, "cancel", ArticleBotCallbackVO.CANCEL),),
            ),
        )

    def _finish_create(self, *, chat_id: int, language: str, admin_user, status: str) -> ArticleBotScreenDTO:
        state = self.state_repository.get(chat_id)
        if state.get("step") != ArticleBotStepEnum.CREATE_STATUS.value:
            self.clear_state(chat_id)
            return self._message_screen(language, "session_expired")
        if status not in ArticleStatusEnum.values():
            raise ValidationError(ArticleBotTextVO.get(language, "invalid_status"))
        data = state.get("data", {})
        article = self.management_logic.create_article(
            actor=admin_user,
            dto=ArticleCreateDTO(
                title=data.get("title", ""),
                excerpt=data.get("excerpt", ""),
                content=data.get("content", ""),
                article_type=data.get("article_type", ArticleTypeEnum.BLOG.value),
                status=status,
            ),
        )
        self.clear_state(chat_id)
        return self._success_then_admin_detail(language, "created", article.id)

    def _start_edit_field(self, *, chat_id: int, language: str, article_id: object, field: str) -> ArticleBotScreenDTO:
        try:
            field_enum = ArticleBotFieldEnum(field)
        except ValueError as exc:
            raise ValidationError(ArticleBotTextVO.get(language, "invalid_field")) from exc
        self.management_logic.get_article(article_id)
        self.state_repository.set(
            chat_id,
            {
                "flow": ArticleBotFlowEnum.EDIT.value,
                "step": ArticleBotStepEnum.EDIT_VALUE.value,
                "article_id": str(article_id),
                "field": field_enum.value,
            },
        )
        return ArticleBotScreenDTO(
            text=ArticleBotTextVO.get(
                language,
                "edit_prompt",
                field=ArticleBotButtonTextVO.get(language, field_enum.value),
            ),
            rows=((self._button(language, "cancel", ArticleBotCallbackVO.CANCEL),),),
        )

    def _consume_state_text(self, *, chat_id: int, language: str, text: str, admin_user, state: dict) -> ArticleBotScreenDTO:
        flow = state.get("flow")
        step = state.get("step")
        if flow == ArticleBotFlowEnum.CREATE.value:
            data = state.setdefault("data", {})
            if step == ArticleBotStepEnum.CREATE_TITLE.value:
                if not text:
                    raise ValidationError(ArticleBotTextVO.get(language, "title_required"))
                data["title"] = text
                state["step"] = ArticleBotStepEnum.CREATE_EXCERPT.value
                self.state_repository.set(chat_id, state)
                return self._prompt_screen(language, "create_excerpt_prompt")
            if step == ArticleBotStepEnum.CREATE_EXCERPT.value:
                data["excerpt"] = "" if text == ArticleBotInputVO.EMPTY_VALUE else text
                state["step"] = ArticleBotStepEnum.CREATE_CONTENT.value
                self.state_repository.set(chat_id, state)
                return self._prompt_screen(language, "create_content_prompt")
            if step == ArticleBotStepEnum.CREATE_CONTENT.value:
                if not text:
                    raise ValidationError(ArticleBotTextVO.get(language, "content_required"))
                data["content"] = text
                state["step"] = ArticleBotStepEnum.CREATE_TYPE.value
                self.state_repository.set(chat_id, state)
                return ArticleBotScreenDTO(
                    text=ArticleBotTextVO.get(language, "create_type_prompt"),
                    rows=(
                        (
                            self._button(language, "blog", ArticleBotCallbackVO.create_type(ArticleTypeEnum.BLOG.value)),
                            self._button(language, "news", ArticleBotCallbackVO.create_type(ArticleTypeEnum.NEWS.value)),
                        ),
                        (self._button(language, "cancel", ArticleBotCallbackVO.CANCEL),),
                    ),
                )
        if flow == ArticleBotFlowEnum.EDIT.value and step == ArticleBotStepEnum.EDIT_VALUE.value:
            value = "" if text == ArticleBotInputVO.EMPTY_VALUE else text
            article = self.management_logic.update_text_field(
                actor=admin_user,
                article_id=state.get("article_id"),
                field=state.get("field", ""),
                value=value,
            )
            self.clear_state(chat_id)
            return self._success_then_admin_detail(language, "updated", article.id)
        self.clear_state(chat_id)
        return self._message_screen(language, "invalid_state")

    def _success_then_admin_detail(self, language: str, key: str, article_id: object) -> ArticleBotScreenDTO:
        detail = self.admin_detail_screen(language=language, article_id=article_id)
        return ArticleBotScreenDTO(text=f"{ArticleBotTextVO.get(language, key)}\n\n{detail.text}", rows=detail.rows)

    def _prompt_screen(self, language: str, key: str) -> ArticleBotScreenDTO:
        return ArticleBotScreenDTO(
            text=ArticleBotTextVO.get(language, key),
            rows=((self._button(language, "cancel", ArticleBotCallbackVO.CANCEL),),),
        )

    def _message_screen(self, language: str, key: str) -> ArticleBotScreenDTO:
        return ArticleBotScreenDTO(
            text=ArticleBotTextVO.get(language, key),
            rows=((self._button(language, "back", ArticleBotCallbackVO.MENU),),),
        )

    def _error_screen(self, language: str, exc: Exception) -> ArticleBotScreenDTO:
        if getattr(exc, "status_code", None) == 404:
            return self._message_screen(language, "not_found")
        detail = getattr(exc, "detail", None)
        if isinstance(exc, ValidationError):
            error = " ".join(exc.messages)
        else:
            error = str(detail or exc)
        return ArticleBotScreenDTO(
            text=ArticleBotTextVO.get(language, "operation_failed", error=html.escape(error)),
            rows=((self._button(language, "back", ArticleBotCallbackVO.MENU),),),
        )

    @staticmethod
    def _positive_int(value: str) -> int:
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 1

    @staticmethod
    def _date(value) -> str:
        if not value:
            return "—"
        try:
            value = timezone.localtime(value)
        except ValueError:
            pass
        return value.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _type_icon(article_type: str) -> str:
        return "📰" if article_type == ArticleTypeEnum.NEWS.value else "✍️"

    def _format_public_row(self, language: str, article) -> str:
        return ArticleBotTextVO.get(
            language,
            "article_row",
            icon=self._type_icon(article.article_type),
            title=html.escape(article.title),
            excerpt=html.escape(Truncator(article.excerpt or strip_tags(article.content or "")).chars(130)),
            date=self._date(article.published_at),
            views=article.view_count,
        )

    def _format_admin_row(self, language: str, article) -> str:
        return ArticleBotTextVO.get(
            language,
            "admin_article_row",
            icon=self._type_icon(article.article_type),
            title=html.escape(article.title),
            type_label=ArticleBotLabelVO.type_label(language, article.article_type),
            status_label=ArticleBotLabelVO.status_label(language, article.status),
            views=article.view_count,
        )

    @staticmethod
    def _button(language: str, key: str, callback_data: str) -> ArticleBotButtonDTO:
        return ArticleBotButtonDTO(
            text=ArticleBotButtonTextVO.get(language, key),
            callback_data=callback_data,
        )

    def _pagination_rows(self, language: str, page_obj, prefix: str, article_type: str):
        buttons = []
        if page_obj.has_previous():
            buttons.append(self._button(language, "previous", f"{prefix}:{article_type}:{page_obj.previous_page_number()}"))
        if page_obj.has_next():
            buttons.append(self._button(language, "next", f"{prefix}:{article_type}:{page_obj.next_page_number()}"))
        return [tuple(buttons)] if buttons else []

    def _admin_pagination_rows(self, language: str, page_obj):
        buttons = []
        if page_obj.has_previous():
            buttons.append(self._button(language, "previous", ArticleBotCallbackVO.admin_list(page_obj.previous_page_number())))
        if page_obj.has_next():
            buttons.append(self._button(language, "next", ArticleBotCallbackVO.admin_list(page_obj.next_page_number())))
        return [tuple(buttons)] if buttons else []
