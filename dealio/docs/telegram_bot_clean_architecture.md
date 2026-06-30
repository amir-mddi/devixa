# Telegram/Bale/Rubika Bot Clean Architecture

The bot entrypoints now follow this flow:

```text
polling command / webhook view
        -> application service
        -> controller
        -> logic
        -> repositories
        -> adapters
```

## Layers

```text
telegram_bot/
  application_services/
    polling_service.py
    rubika_polling_service.py
    webhook_service.py

  controllers/
    update_controller.py

  logic/
    update_process_logic.py

  repositories/
    bot_cache_repository.py
    bot_runtime_repository.py
    profile_repository.py
    update_log_repository.py
    user_role_repository.py
    adapters/
      redis_cache_adapter.py
      postgres_bot_adapter.py
      telegram_api_adapter.py
      bot_runtime_adapter.py

  interfaces/
    bot_client_interface.py

  services.py
    Backwards-compatible bot runtime/facade. Existing bot flows are preserved,
    while infrastructure access is moved behind repositories/adapters.
```

## Rules

- Views and management commands are thin controllers/application services.
- Redis/cache access goes through `TelegramBotCacheRepository`.
- PostgreSQL/ORM access for profiles/update logs/user-role setup goes through repositories/adapters.
- Telegram HTTP API calls go through `TelegramApiAdapter`.
- Update processing is idempotent through `TelegramUpdateLogRepository`.
- Existing course/billing/review logic remains reused through the commerce logic repository.

## Next recommended steps

The remaining large compatibility runtime in `services.py` can be split feature by feature into:

- `logic/account_link_logic.py`
- `logic/account_creation_logic.py`
- `logic/course_message_logic.py`
- `logic/admin_course_message_logic.py`
- `logic/review_message_logic.py`
- `logic/channel_invite_logic.py`
- `renderers/message_renderer.py`
- `renderers/keyboard_renderer.py`

Do this incrementally to avoid changing bot behavior in one risky rewrite.
