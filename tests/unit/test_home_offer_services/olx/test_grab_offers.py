import asyncio
import os
import unittest
from typing import Sequence
from unittest import TestCase

from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

from scraping_lib.download_html_home_offers.olx import olx_download_html_home_offers
from scraping_lib.scraping.olx import OlxScrapper
from src.home_offer.model import HouseOfferModel
from src.home_offer.services import HomeOfferService
from src.scraping_lib.constants import PROJECT_ROOT
from src.utils.models import BaseModel
from src.utils.others import str_env_to_bool


class TestHomeOffer(TestCase):
    EURO_TO_ZLOTYS = 4.3

    def setUp(self) -> None:
        super().setUp()
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        self.engine = engine
        self.download_html_home_offers_service = olx_download_html_home_offers
        self.service = HomeOfferService(
            engine,
            download_html_home_offers_service=self.download_html_home_offers_service,
            scraper=OlxScrapper()
        )

    def tearDown(self) -> None:
        super().tearDown()
        BaseModel.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_grab_offers(self):
        asyncio.run(self.service.grab_offers())
        with Session(self.engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            self.assertGreaterEqual(len(offers), 10)

    @unittest.skipIf(not str_env_to_bool(os.getenv("IS_TEST_WITH_REAL_DB")), "use real db. For check work with real db")
    def test_grab_offers_with_real_db(self):
        path = f"sqlite:///{PROJECT_ROOT}/data/db-test-olx.sqlite"
        engine = create_engine(path)
        BaseModel.metadata.create_all(engine)

        asyncio.run(
            HomeOfferService(
                engine=engine,
                download_html_home_offers_service=self.download_html_home_offers_service,
                scraper=OlxScrapper()
            ).grab_offers()
        )
        with Session(engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            length_offers = len(offers)

            self.assertGreaterEqual(length_offers, 10)
        engine.dispose()
