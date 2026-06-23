import os

from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dealio.project.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
import logging

logger = logging.getLogger("dealio")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
        ])
    ),
})

logger.info("ASGI application started and routing is set")
