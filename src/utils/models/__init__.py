from typing import TYPE_CHECKING

from src.utils.models.base_model import BaseModel

if TYPE_CHECKING:
    from src.home_offer.money.model import MoneyModel
if TYPE_CHECKING:
    from src.home_offer.model import HouseOfferModel

__all__ = [
    "BaseModel",
    "MoneyModel",
    "HouseOfferModel"
]
