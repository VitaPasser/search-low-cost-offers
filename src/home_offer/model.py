from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.models import BaseModel


class HouseOfferModel(BaseModel):
    __tablename__ = "house_offers"

    id_url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    price_id: Mapped[int] = mapped_column(ForeignKey("money.id"), nullable=False)
    price: Mapped["MoneyModel"] = relationship(
        foreign_keys=[price_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    tax_id: Mapped[int | None] = mapped_column(ForeignKey("money.id"), nullable=True)
    tax: Mapped[Optional["MoneyModel"]] = relationship(
        foreign_keys=[tax_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    deposit_id: Mapped[int | None] = mapped_column(ForeignKey("money.id"), nullable=True)
    deposit: Mapped[Optional["MoneyModel"]] = relationship(
        foreign_keys=[deposit_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    realtor_service_id: Mapped[int | None] = mapped_column(ForeignKey("money.id"), nullable=True)
    realtor_service: Mapped[Optional["MoneyModel"]] = relationship(
        foreign_keys=[realtor_service_id],
        cascade="all, delete-orphan",
        single_parent=True
    )
    is_has_been_realtor_services: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)
