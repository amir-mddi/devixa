import random

from dealio.project.settings import LIST_OF_PROXIES


class ProxyUrls:
    URLS = [
        {"http": f"http://{proxy}"}
        for proxy in LIST_OF_PROXIES.split(',') if proxy != ''
    ]

    @classmethod
    def get_proxy(cls):
        return random.choice(cls.URLS) if len(cls.URLS) > 0 else None
