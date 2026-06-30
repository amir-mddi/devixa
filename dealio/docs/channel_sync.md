# Channel Sync

Channel sync is now handled by a dedicated management command instead of the normal user bot polling command.

## Flow

```text
Telegram source channel post/edit
    -> channel_sync_polling
    -> Bale target chat/channel
    -> Rubika target chat/channel

Bale source channel post/edit/delete
    -> channel_sync_polling
    -> Telegram target channel
```

The sync stores a mapping in `ChannelSyncMessage` so edits/deletes can affect the related target message instead of creating duplicates.

## Important

Run only one update consumer per bot token. If `telegram_polling` and `channel_sync_polling --provider telegram` run at the same time for the same Telegram token, one of them may consume the channel update first.

For channel sync, run:

```bash
python -m dealio.project.manage channel_sync_polling --provider all
```

Or run only one source:

```bash
python -m dealio.project.manage channel_sync_polling --provider telegram
python -m dealio.project.manage channel_sync_polling --provider bale
```

## Required env

```env
CHANNEL_SYNC_ENABLED=true

# Telegram source -> Bale/Rubika
CHANNEL_SYNC_TELEGRAM_SOURCE_CHAT_ID=-1001234567890
CHANNEL_SYNC_BALE_TARGET_CHAT_ID=2
CHANNEL_SYNC_RUBIKA_TARGET_CHAT_ID=your_rubika_target_chat_id

# Bale source -> Telegram
CHANNEL_SYNC_BALE_SOURCE_CHAT_ID=2
CHANNEL_SYNC_TELEGRAM_TARGET_CHAT_ID=-1001234567890
```

`CHANNEL_SYNC_TELEGRAM_SOURCE_CHAT_ID` and `CHANNEL_SYNC_TELEGRAM_TARGET_CHAT_ID` may be the same channel when you want a two-way Telegram/Bale sync.

## Invite links

These are user-facing links shown by `/channels`.

```env
CHANNEL_INVITE_TELEGRAM_URL=https://t.me/your_telegram_channel
CHANNEL_INVITE_BALE_URL=https://ble.ir/your_bale_channel
CHANNEL_INVITE_RUBIKA_URL=https://rubika.ir/your_rubika_channel
```

## Testing Telegram -> Bale

1. Add Telegram bot as admin in Telegram source channel.
2. Add Bale bot to Bale target chat/channel.
3. Set `CHANNEL_SYNC_TELEGRAM_SOURCE_CHAT_ID` and `CHANNEL_SYNC_BALE_TARGET_CHAT_ID`.
4. Run:

```bash
python -m dealio.project.manage channel_sync_polling --provider telegram
```

5. Send a new message in the Telegram source channel.
6. The message should appear in Bale.
7. Edit the Telegram message.
8. The Bale message should be edited.

## Testing Bale -> Telegram

1. Add Bale bot to Bale source chat/channel.
2. Add Telegram bot as admin in Telegram target channel with post/edit/delete permissions.
3. Set `CHANNEL_SYNC_BALE_SOURCE_CHAT_ID` and `CHANNEL_SYNC_TELEGRAM_TARGET_CHAT_ID`.
4. Run:

```bash
python -m dealio.project.manage channel_sync_polling --provider bale
```

5. Send a new message in Bale source chat/channel.
6. The message should appear in Telegram.
7. Edit the Bale message.
8. The Telegram message should be edited.
9. Delete the Bale message if Bale Bot API sends a delete update for your chat type; the Telegram copy should be deleted.

## Delete support note

Telegram Bot API does not provide deleted channel post updates. Bale delete sync works only when Bale sends a delete event in `getUpdates`. The code supports common delete payload names such as `deleted_message` and `deleted_channel_post`.

## Echo-loop protection

If you run `channel_sync_polling --provider all`, the message that your bot sends to the target provider may also appear in that provider's `getUpdates` result. The sync logic now prevents this loop in three ways:

1. Ignore messages authored by bot accounts when the provider exposes `from.is_bot` or `sender_type=Bot`.
2. Ignore messages already stored as a target mapping in `ChannelSyncMessage`.
3. Ignore very recent target messages with the same text hash in the same target chat, which covers providers that return a different message id in updates than the id returned by `sendMessage`.

For one-way testing, prefer:

```bash
python -m dealio.project.manage channel_sync_polling --provider telegram
```

For two-way testing, use:

```bash
python -m dealio.project.manage channel_sync_polling --provider all
```

## Manual delete fallback

Telegram Bot API does not send delete events for deleted channel posts. If the source message was Telegram and you deleted it, automatic deletion of Bale/Rubika copies is not possible through Bot API polling.

Use this manual fallback when you know the original source message id:

```bash
python -m dealio.project.manage channel_sync_delete \
  --source-provider telegram \
  --source-chat-id -1001234567890 \
  --source-message-id 45
```

For Bale source deletes, automatic delete sync works only if Bale returns a delete update. If it does not, use the same command with Bale source values:

```bash
python -m dealio.project.manage channel_sync_delete \
  --source-provider bale \
  --source-chat-id 2 \
  --source-message-id 33
```

## Media sync support

The channel sync now supports these message types when the provider exposes a bot-accessible file id or URL:

```text
Telegram photo/video/document -> Bale photo/video/document
Telegram photo/video/document -> Rubika fallback text + media URL
Bale photo/video/document -> Telegram photo/video/document when Bale update exposes file URL or getFile returns URL
```

For Telegram source media, the sync resolves Telegram `file_id` with `getFile`, builds a temporary bot file URL, and sends that media URL to the target provider. Bale targets use `sendPhoto`, `sendVideo`, or `sendDocument`.

Rubika Bot API media upload is provider-specific and may require Rubika file ids. Until a Rubika upload/getFile adapter is available, Rubika receives a text fallback containing the caption and media URL.

## Delete sync behavior

Automatic delete sync works only when the source provider sends a delete update. Bale delete updates are handled in both directions:

```text
Bale original message deleted -> Telegram mirrored message deleted
Bale mirrored message deleted -> Telegram original source message deleted
```

Telegram Bot API does not deliver deleted channel post updates, so deleting the original Telegram channel post cannot be detected by polling. Use `channel_sync_delete` for Telegram-source deletes.
