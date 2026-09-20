from datetime import datetime

from sqlmodel import Field, Relationship

from src.home_offer.money.model import MoneyModel
from src.utils.models import BaseModel


class HouseOfferModel(BaseModel, table=True):
    __tablename__ = "house_offers"

    id_url: str = Field(unique=True)
    url: str = Field(unique=True)

    price_id: int | None = Field(default=None, foreign_key="money.id")
    price: MoneyModel = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "HouseOfferModel.price_id == MoneyModel.id",
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "lazy": "selectin"
        }
    )

    tax_id: int | None = Field(default=None, foreign_key="money.id")
    tax: MoneyModel | None = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "HouseOfferModel.tax_id == MoneyModel.id",
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "lazy": "selectin"
        }
    )

    deposit_id: int | None = Field(default=None, foreign_key="money.id")
    deposit: MoneyModel | None = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "HouseOfferModel.deposit_id == MoneyModel.id",
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "lazy": "selectin"
        }
    )

    realtor_service_id: int | None = Field(default=None, foreign_key="money.id")
    realtor_service: MoneyModel | None = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "HouseOfferModel.realtor_service_id == MoneyModel.id",
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "lazy": "selectin"
        }
    )

    is_has_been_realtor_services: bool

    created_at: datetime|None = Field(default_factory=datetime.now, nullable=False)
