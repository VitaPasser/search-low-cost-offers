import os
import unittest
from typing import Sequence
from unittest import TestCase

from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

from src.home_offer.model import HouseOfferModel
from src.home_offer.services import HomeOfferService
from src.scraping_lib.constants import PROJECT_ROOT
from src.scraping_lib.download_html_home_offers.otodom import otodom_download_html_home_offers
from src.scraping_lib.scraping.otodom import OtodomScrapper
from src.utils.models import BaseModel
from src.utils.others import str_env_to_bool


class TestHomeOffer(TestCase):
    EURO_TO_ZLOTYS = 4.3

    def setUp(self) -> None:
        super().setUp()
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        self.engine = engine
        self.download_html_home_offers_service = otodom_download_html_home_offers
        self.service = HomeOfferService(
            engine,
            download_html_home_offers_service=self.download_html_home_offers_service,
            scraper=OtodomScrapper()
        )

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

    @unittest.skipIf(not str_env_to_bool(os.getenv("IS_TEST_WITH_REAL_DB")), "use real db. For check work with real db")
    def test_grab_offers_with_real_db(self):
        path = f"sqlite:///{PROJECT_ROOT}/data/db-test-otodom.sqlite"
        engine = create_engine(path)
        BaseModel.metadata.create_all(self.engine)
        HomeOfferService(
            engine=engine,
            download_html_home_offers_service=self.download_html_home_offers_service,
            scraper=OtodomScrapper()
        ).grab_offers()
        with Session(engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            length_offers = len(offers)

            self.assertGreaterEqual(length_offers, 10)
        self.engine.dispose()
