from backend.apps.articles.dtos import ArticleCreateDTO, ArticleUpdateDTO
from backend.apps.articles.logic import ArticleManagementLogic


class AdminArticleLogic:
    def __init__(self, article_logic: ArticleManagementLogic | None = None):
        self.article_logic = article_logic or ArticleManagementLogic()

    def list_articles(self, filters: dict | None = None):
        return self.article_logic.list_articles(filters or {})

    def paginate_articles(
        self,
        filters: dict | None = None,
        *,
        page: object = 1,
        page_size: int = 20,
    ):
        return self.article_logic.paginate_articles(
            filters or {},
            page=page,
            page_size=page_size,
        )

    def get_article(self, article_id):
        return self.article_logic.get_article(article_id)

    def list_categories(self):
        return self.article_logic.list_categories()

    def list_tags(self):
        return self.article_logic.list_tags()

    def list_article_tag_ids(self, article_id):
        return self.article_logic.list_article_tag_ids(article_id)

    def create_article(self, *, actor, data: dict):
        return self.article_logic.create_article(
            actor=actor,
            dto=ArticleCreateDTO(**data),
        )

    def update_article(self, *, actor, article_id, data: dict):
        return self.article_logic.update_article(
            actor=actor,
            dto=ArticleUpdateDTO(article_id=article_id, **data),
        )

    def delete_article(self, *, actor, article_id):
        return self.article_logic.delete_article(actor=actor, article_id=article_id)
