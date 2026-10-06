from enum import StrEnum


class TelegramMemberStatusEnum(StrEnum):
    CREATOR = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    KICKED = "kicked"

    @classmethod
    def active_values(cls) -> frozenset[str]:
        return frozenset(
            {
                cls.CREATOR.value,
                cls.ADMINISTRATOR.value,
                cls.MEMBER.value,
                cls.RESTRICTED.value,
            }
        )
