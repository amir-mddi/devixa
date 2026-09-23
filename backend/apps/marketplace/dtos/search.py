from dataclasses import dataclass


@dataclass(frozen=True)
class MarketplaceSearch:
    query: str = ""
    city: str = ""
    subject: str = ""
    mode: str = ""
    maximum_price: str = ""
