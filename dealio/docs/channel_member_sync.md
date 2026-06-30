# Channel Member Sync

This command audits known cross-provider bot users and sends invite links when a
known user exists on one messenger but is missing from the other channel.

## Important API limitation

Bots cannot force-add arbitrary users to Telegram channels. The supported and
safe behavior is:

1. check a known user's membership when the provider API supports it;
2. send the missing channel invite link to that user's private bot chat.

Bale also exposes member lookup and invite-related APIs, but this project keeps
the behavior consistent and permission-safe by sending invite links instead of
forcing joins.

## Required env

```env
CHANNEL_MEMBER_SYNC_TELEGRAM_CHAT_ID=-1001234567890
CHANNEL_MEMBER_SYNC_BALE_CHAT_ID=2
CHANNEL_INVITE_TELEGRAM_URL=https://t.me/your_telegram_channel
CHANNEL_INVITE_BALE_URL=https://ble.ir/your_bale_channel
```

The command uses existing `TelegramProfile` rows. A user can only be compared
across Telegram/Bale when both profiles are linked to the same Dealio user.

## Dry-run

```bash
python -m dealio.project.manage channel_member_sync --direction both
```

## Execute invitations

```bash
python -m dealio.project.manage channel_member_sync --direction both --execute
```

## Direction-specific commands

Telegram users missing from Bale get Bale invite via Telegram private chat:

```bash
python -m dealio.project.manage channel_member_sync --direction telegram-to-bale --execute
```

Bale users missing from Telegram get Telegram invite via Bale private chat:

```bash
python -m dealio.project.manage channel_member_sync --direction bale-to-telegram --execute
```
