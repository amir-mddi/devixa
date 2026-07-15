from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelSyncTargetDTO:
    provider: str
    chat_id: str


@dataclass(frozen=True)
class ChannelMediaDTO:
    """Normalized media payload used by channel sync.

    file_id is the provider-side file identifier from the source update.
    file_url is an HTTP URL that target providers can fetch when they support
    remote URL uploads. It is resolved inside the adapter/logic layer, not in
    controllers or management commands.
    """

    media_type: str
    file_id: str = ""
    file_url: str = ""
    mime_type: str = ""
    file_name: str = ""

    @property
    def has_media(self) -> bool:
        return bool(self.media_type and (self.file_id or self.file_url))


@dataclass(frozen=True)
class ChannelPostDTO:
    source_provider: str
    source_chat_id: str
    source_message_id: str
    text: str = ""
    is_edit: bool = False
    is_delete: bool = False
    media: ChannelMediaDTO | None = None

    @property
    def has_media(self) -> bool:
        return bool(self.media and self.media.has_media)
