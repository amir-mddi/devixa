from __future__ import annotations

from asgiref.sync import sync_to_async


async def validate_serializer(serializer):
    """Run DRF validation in Django's thread-sensitive executor."""
    await sync_to_async(serializer.is_valid, thread_sensitive=True)(raise_exception=True)
    return serializer


async def serializer_data(serializer):
    """Evaluate serializer data outside the event loop.

    Accessing ``serializer.data`` can evaluate lazy ORM relations, so it must not
    run directly inside an async request handler.
    """
    return await sync_to_async(lambda: serializer.data, thread_sensitive=True)()


async def call_sync(callable_, /, *args, **kwargs):
    """Run a synchronous Django/DRF compatibility boundary safely."""
    return await sync_to_async(callable_, thread_sensitive=True)(*args, **kwargs)


async def call_async_method(
    target,
    async_method_name: str,
    sync_method_name: str,
    /,
    *args,
    thread_sensitive: bool = True,
    **kwargs,
):
    """Call a native async method with a legacy sync fallback.

    This keeps production request paths async while allowing existing injected
    test doubles and third-party implementations to expose the old sync contract.
    """
    async_method = getattr(target, async_method_name, None)
    if async_method is not None:
        return await async_method(*args, **kwargs)
    sync_method = getattr(target, sync_method_name)
    return await sync_to_async(
        sync_method,
        thread_sensitive=thread_sensitive,
    )(*args, **kwargs)
