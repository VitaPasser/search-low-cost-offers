import unittest
from typing import Sequence
from unittest import TestCase

from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

from home_offer.services import grab_offers
from src.home_offer.model import HouseOfferModel
from src.utils.models import BaseModel


class TestHomeOffer(TestCase):

    def setUp(self) -> None:
        super().setUp()
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        self.engine = engine

    def tearDown(self) -> None:
        super().tearDown()
        BaseModel.metadata.drop_all(self.engine)

    def test_grab_offers(self):
        grab_offers(self.engine)
        with Session(self.engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            self.assertGreaterEqual(len(offers), 10)

    # @unittest.skip("use real db. For check work with real db")
    def test_grab_offers_with_real_db(self):
        from utils.db.sqlalchemy import engine
        grab_offers(engine)
        length_offers = 0
        with Session(engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            length_offers = len(offers)

        self.assertGreaterEqual(length_offers, 10)
