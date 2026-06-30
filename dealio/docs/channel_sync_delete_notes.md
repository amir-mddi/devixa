# Channel sync delete notes

## Important provider limitation

Telegram Bot API does not deliver `channel_post_deleted` updates. Because of that, if the original Telegram channel message is deleted, polling cannot automatically know it was deleted.

Use the manual delete command with the exact source message ID from the mapping table:

```bash
python -m dealio.project.manage channel_sync_delete --show-recent

python -m dealio.project.manage channel_sync_delete \
  --source-provider telegram \
  --source-chat-id -1001234567890 \
  --source-message-id 45
```

If you only know the mirrored Bale message ID and want to delete the related Telegram source message:

```bash
python -m dealio.project.manage channel_sync_delete \
  --target-provider bale \
  --target-chat-id 2 \
  --target-message-id 33
```

If you want to delete one exact message directly, bypassing mappings:

```bash
python -m dealio.project.manage channel_sync_delete \
  --direct-provider bale \
  --direct-chat-id 2 \
  --direct-message-id 33
```

## Why "No synced mapping" happens

The message ID must be the exact `source_message_id` saved in `ChannelSyncMessage`.
Old messages created before sync was enabled will not have mappings.

Run:

```bash
python -m dealio.project.manage channel_sync_delete --show-recent --limit 30
```

Then copy the exact `source=(provider, chat, msg)` values from the output.
