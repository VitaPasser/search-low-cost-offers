import asyncio
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.home_offer.dto import HouseOfferDTO
from src.home_offer.dto import HouseOfferSumDTO
from src.home_offer.model import HouseOfferModel
from src.home_offer.money.cuerrency.model import Currency
from src.home_offer.services import HomeOfferService
from src.scraping_lib.download_html_home_offers.otodom import otodom_download_html_home_offers
from src.scraping_lib.scraping.otodom import OtodomScrapper
from src.utils.models import BaseModel


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

    def test_sort_get_all(self):
        asyncio.run(self.service.grab_offers(True))
        offers = self.service.get_all()
        self.assertGreaterEqual(len(offers), 10)
        self.__assertAscSort(offers)

    def test_get_all_in_euro(self):
        asyncio.run(self.service.grab_offers(True))
        offers = self.service.get_in_euro_all()
        self.assertGreaterEqual(len(offers), 10)
        for offer in offers:
            self.assertEqual(offer.price.currency, Currency.EUR)

    def test_sort_get_all_in_euro(self):
        asyncio.run(self.service.grab_offers(True))
        offers = self.service.get_in_euro_all()
        self.assertGreaterEqual(len(offers), 10)
        for index, offer in enumerate(offers[1:], 1):
            self.assertLessEqual(offers[index - 1].price.amount, offer.price.amount)

    def test_get_all_in_euro_and_sum_with_tax(self):
        asyncio.run(self.service.grab_offers(True))
        offers_with_sum = self.service.get_in_euro_all_and_sum_with_tax()
        self.assertGreaterEqual(len(offers_with_sum), 10)
        with Session(self.engine) as session:
            for offer in offers_with_sum:
                offer_reference = session.query(HouseOfferModel).where(HouseOfferModel.id == offer.id).first()
                self.assertIsNotNone(offer_reference)
                if offer_reference is None: return  # for suppress the warning
                self.assertEqual(result.amount if (result := offer.price) else result,
                                 (offer_reference.price.amount + offer_reference.tax.amount) / self.EURO_TO_ZLOTYS
                                 if offer_reference.tax else None)

    def test_sort_get_all_in_euro_and_sum_with_tax(self):
        asyncio.run(self.service.grab_offers(True))
        offers_with_sum = self.service.get_in_euro_all_and_sum_with_tax()
        self.assertGreaterEqual(len(offers_with_sum), 10)
        self.__assertAscSort(offers_with_sum)

    def test_get_all_in_euro_and_sum_with_tax_and_deposit(self):
        asyncio.run(self.service.grab_offers(True))
        offers_with_sum = self.service.get_in_euro_all_and_sum_with_tax_and_deposit()
        self.assertGreaterEqual(len(offers_with_sum), 10)
        with Session(self.engine) as session:
            for offer in offers_with_sum:
                offer_reference = session.query(HouseOfferModel).where(HouseOfferModel.id == offer.id).first()
                self.assertIsNotNone(offer_reference)
                if offer_reference is None: return  # for suppress the warning
                self.assertEqual(result.amount if (result := offer.price) else result,
                                 (
                                         offer_reference.price.amount + offer_reference.tax.amount + offer_reference.deposit.amount) / self.EURO_TO_ZLOTYS
                                 if offer_reference.tax and offer_reference.deposit else None)

    def test_sort_get_all_in_euro_and_sum_with_tax_and_deposit(self):
        asyncio.run(self.service.grab_offers(True))
        offers_with_sum = self.service.get_in_euro_all_and_sum_with_tax_and_deposit()
        self.assertGreaterEqual(len(offers_with_sum), 10)
        self.__assertAscSort(offers_with_sum)

    def __assertAscSort(self, offers_with_sum: list[HouseOfferDTO | HouseOfferSumDTO]):
        for index, offer in enumerate(offers_with_sum[1:], 1):
            actual = result.amount if (result := offers_with_sum[index - 1].price) else None
            expect = result.amount if (result := offer.price) else None
            if actual is None or expect is None:
                continue
            else:
                self.assertLessEqual(actual, expect)

    def test_get_all_in_euro_and_sum_with_tax_deposit_and_realtor(self):
        asyncio.run(self.service.grab_offers(True))
        offers_with_sum = self.service.get_in_euro_all_and_sum_with_tax_deposit_and_realtor()
        self.assertGreaterEqual(len(offers_with_sum), 10)
        with Session(self.engine) as session:
            offer = session.query(HouseOfferModel).where(HouseOfferModel.id_url == offers_with_sum[0].id_url).first()
            self.assertIsNotNone(offer)
            if offer is None: return  # for suppress the warning
            self.assertEqual(result.amount if (result := offers_with_sum[0].price) else result,
                             (offer.price.amount + offer.tax.amount
                              + offer.deposit.amount + offer.realtor_service.amount) / self.EURO_TO_ZLOTYS
                             if offer.tax and offer.deposit and offer.realtor_service else None)

    def test_sort_when_get_all_in_euro_and_sum_with_tax_deposit_and_realtor(self):
        asyncio.run(self.service.grab_offers(True))
        offers_with_sum = self.service.get_in_euro_all_and_sum_with_tax_deposit_and_realtor()
        self.assertGreaterEqual(len(offers_with_sum), 10)
        self.__assertAscSort(offers_with_sum)
