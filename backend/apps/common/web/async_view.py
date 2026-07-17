from __future__ import annotations

import inspect

from asgiref.sync import sync_to_async


class AsyncWebViewMixin:
    """ASGI-safe bridge for Django's synchronous HTML class-based views.

    Django 5.2 supports async views, but template rendering, forms, messages,
    sessions, several authentication mixins, and transaction blocks are still
    predominantly synchronous. This mixin makes the outer controller and
    dispatch path genuinely asynchronous while preserving the complete Django
    mixin chain in the thread-sensitive executor.
    """

    view_is_async = True

    async def dispatch(self, request, *args, **kwargs):
        dispatch_method = super().dispatch
        if inspect.iscoroutinefunction(dispatch_method):
            response = await dispatch_method(request, *args, **kwargs)
        else:
            response = await sync_to_async(
                dispatch_method,
                thread_sensitive=True,
            )(request, *args, **kwargs)
        if inspect.isawaitable(response):
            return await response
        return response
