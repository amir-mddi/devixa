from enum import Enum


class BaseEnum(str, Enum):
    @classmethod
    def choices(cls):
        return [(tag.value.lower(), tag.name.title()) for tag in cls]

    @classmethod
    def values(cls, lower: bool = False):
        return [tag.value.lower() if lower else tag.value for tag in cls]
