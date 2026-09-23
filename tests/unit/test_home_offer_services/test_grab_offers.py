import unittest
from typing import Sequence
from unittest import TestCase

from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

from src.home_offer.model import HouseOfferModel
from src.home_offer.services import HomeOfferService
from src.scraping_lib.constants import OTODOM_NAME, OTODOM_URL_LIST, OTODOM_DOMAIN_URL
from src.scraping_lib.download_html_home_offers import pagination_max_number_scraper, DownloadHtmlHomeOffersService
from src.scraping_lib.scraping.otodom import OtodomScrapper
from src.utils.models import BaseModel


class TestHomeOffer(TestCase):
    EURO_TO_ZLOTYS = 4.3

    def setUp(self) -> None:
        super().setUp()
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        self.engine = engine
        self.download_html_home_offers_service = DownloadHtmlHomeOffersService(
            domain_url=OTODOM_DOMAIN_URL,
            url_list=OTODOM_URL_LIST,
            name=OTODOM_NAME,
            pagination_number_max_scraper=pagination_max_number_scraper
        )
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

    @unittest.skip("use real db. For check work with real db")
    def test_grab_offers_with_real_db(self):
        from src.utils.db.sqlalchemy import engine
        HomeOfferService(
            engine=engine,
            download_html_home_offers_service=self.download_html_home_offers_service,
            scraper=OtodomScrapper()
        ).grab_offers()
        length_offers = 0
        with Session(engine) as session:
            stmt = Select(HouseOfferModel)
            offers: Sequence[HouseOfferModel] = session.scalars(stmt).all()
            length_offers = len(offers)

        self.assertGreaterEqual(length_offers, 10)
