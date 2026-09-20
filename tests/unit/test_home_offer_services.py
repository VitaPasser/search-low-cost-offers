import unittest
from pprint import pprint
from typing import Sequence
from unittest import TestCase

from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

from home_offer.dto import HouseOfferRead
from src.home_offer.money.cuerrency.model import Currency
from src.home_offer.services import HomeOfferService
from src.home_offer.model import HouseOfferModel
from src.utils.models import BaseModel


class TestHomeOffer(TestCase):

    def setUp(self) -> None:
        super().setUp()
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        self.engine = engine
        self.service = HomeOfferService(engine)

    def tearDown(self) -> None:
        super().tearDown()
        BaseModel.metadata.drop_all(self.engine)
        self.engine.dispose()


    def test_grab_offers(self):
        self.service.grab_offers()
        with Session(self.engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            self.assertGreaterEqual(len(offers), 10)


    def test_get_all(self):
        self.service.grab_offers(True)
        offers = self.service.get_all()
        self.assertGreaterEqual(len(offers), 10)
        pprint([offer.model_dump() for offer in offers])


    def test_get_all_in_euro(self):
        self.service.grab_offers(True)
        offers = self.service.get_in_euro_all()
        self.assertGreaterEqual(len(offers), 10)
        for offer in offers:
            self.assertEqual(offer.price.currency, Currency.EUR)
        pprint([offer.model_dump() for offer in offers])



    @unittest.skip("use real db. For check work with real db")
    def test_grab_offers_with_real_db(self):
        from src.utils.db.sqlalchemy import engine
        HomeOfferService(engine).grab_offers()
        length_offers = 0
        with Session(engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            length_offers = len(offers)

        self.assertGreaterEqual(length_offers, 10)
