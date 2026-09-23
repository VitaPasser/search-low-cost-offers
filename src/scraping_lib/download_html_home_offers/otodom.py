import asyncio

from bs4 import BeautifulSoup

from src.scraping_lib.download_html_home_offers.service import DownloadHtmlHomeOffersService


def pagination_max_number_scraper(html: str) -> int:
    bs = BeautifulSoup(html, "lxml")
    pagination_list = bs.find("ul", attrs={"data-nx-name": "Pagination"})
    if not pagination_list:
        raise IOError
    pagination_elements = pagination_list.find_all("li")
    if not pagination_elements:
        raise IOError
    pagination_number_max = int(pagination_elements[-2].text)
    return pagination_number_max


otodom_download_html_home_offers = DownloadHtmlHomeOffersService(
        domain_url="https://www.otodom.pl",
        url_list="https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie,2-pokoje/lodzkie/lodz/lodz/lodz?limit=36&priceMax=1700&by=DEFAULT&direction=DESC",
        name="otodom",
        pagination_number_max_scraper=pagination_max_number_scraper
    )


if __name__ == "__main__":
    asyncio.run(otodom_download_html_home_offers.save_session())