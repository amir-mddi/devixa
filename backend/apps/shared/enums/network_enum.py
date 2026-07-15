from typing import Self, Optional, List

from pydantic import (
    StrictStr,
)
from rest_framework.exceptions import NotFound

from backend.apps.core_models.dtos.base_dto import BaseDTO
from backend.apps.core_models.enum.base import BaseEnum


class BaseProjectTypeDTO(BaseDTO):
    code: StrictStr
    type: StrictStr


class BaseNetworkDTO(BaseProjectTypeDTO):
    ...


class NetworkType(BaseEnum):
    LTC = BaseNetworkDTO(code="LTC", type="UTXO")
    BTC = BaseNetworkDTO(code="BTC", type="UTXO")
    BCH = BaseNetworkDTO(code="BCH", type="UTXO")
    ETH = BaseNetworkDTO(code="ETH", type="EVM")
    BSC = BaseNetworkDTO(code="BSC", type="EVM")
    TRX = BaseNetworkDTO(code="TRX", type="EVM")
    DOGE = BaseNetworkDTO(code="DOGE", type="UTXO")
    MATIC = BaseNetworkDTO(code="MATIC", type="EVM")
    # TON = BaseNetworkDTO(code="TON", type="EVM")
    XRP = BaseNetworkDTO(code="XRP", type="EVM")

    def __init__(self, network: BaseNetworkDTO) -> None:
        super().__init__()
        self.model = network
        self.code = network.code
        self.type = network.type

    @classmethod
    def get_codes(cls) -> List[str]:
        return [tag.code for tag in cls]

    @classmethod
    def get_network_by_code(cls, code: str) -> Self:
        for _, member in cls.__members__.items():
            if member.code == code:
                return member
        raise NotFound("Invalid Network Type Code Input")

    @classmethod
    def get_network_by_type(cls, type_networks: Optional[str] = None) -> Self:
        networks = []
        for _, member in cls.__members__.items():
            if type_networks is None or member.type == type_networks:
                networks.append(member.code)
        if len(networks) == 0:
            raise NotFound("Invalid Network Type Input")
        return networks

    @classmethod
    def choices_list(cls, filter_param: Optional[str] = None):
        return tuple([(tag.value.code, tag.name.title()) for tag in cls if filter_param and tag.type == filter_param])
