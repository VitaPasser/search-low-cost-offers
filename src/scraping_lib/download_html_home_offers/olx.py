import asyncio

from bs4 import BeautifulSoup

from src.scraping_lib.download_html_home_offers.service import DownloadHtmlHomeOffersService


def pagination_max_number_scraper(html: str, retries: int = 0) -> int:
    if retries > 5:
        raise IOError
    bs = BeautifulSoup(html, "lxml")
    pagination_list = bs.find("nav", attrs={"data-nx-name": "NexusPagination"})
    if not pagination_list:
        raise IOError
    pagination_elements = pagination_list.find_all("li")
    if not pagination_elements:
        raise IOError
    pagination_number_max = int(pagination_elements[-2].text)
    return pagination_number_max


olx_download_html_home_offers = DownloadHtmlHomeOffersService(
        domain_url="https://www.olx.ro",
        url_list="https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/2-camere/bucuresti/?currency=EUR&search%5Bfilter_float_price:to%5D=400",
        name="olx",
        pagination_number_max_scraper=pagination_max_number_scraper
    )


if __name__ == "__main__":
    asyncio.run(olx_download_html_home_offers.save_session())