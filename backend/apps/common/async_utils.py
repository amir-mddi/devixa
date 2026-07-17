from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from asgiref.sync import async_to_sync, sync_to_async

T = TypeVar("T")


async def call_maybe_async(callable_obj: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Call a dependency without blocking the event loop.

    Native async callables are awaited directly. Legacy synchronous adapters are
    executed in Django's thread-sensitive worker so ORM connections and other
    thread-affine resources remain safe during incremental async migration.
    """

    if inspect.iscoroutinefunction(callable_obj):
        return await callable_obj(*args, **kwargs)

    result = await sync_to_async(callable_obj, thread_sensitive=True)(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


def run_async_from_sync(async_callable: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Execute an async callable from an explicitly synchronous framework edge."""

    return async_to_sync(async_callable)(*args, **kwargs)
