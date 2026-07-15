from enum import StrEnum


class ArticleBotFlowEnum(StrEnum):
    CREATE = "create"
    EDIT = "edit"


class ArticleBotStepEnum(StrEnum):
    CREATE_TITLE = "create_title"
    CREATE_EXCERPT = "create_excerpt"
    CREATE_CONTENT = "create_content"
    CREATE_TYPE = "create_type"
    CREATE_STATUS = "create_status"
    EDIT_VALUE = "edit_value"


class ArticleBotFieldEnum(StrEnum):
    TITLE = "title"
    EXCERPT = "excerpt"
    CONTENT = "content"
    SOURCE_NAME = "source_name"
    SOURCE_URL = "source_url"
    META_TITLE = "meta_title"
    META_DESCRIPTION = "meta_description"
