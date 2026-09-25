import asyncio

from bs4 import BeautifulSoup

from src.scraping_lib.download_html_home_offers.service import DownloadHtmlHomeOffersService


def pagination_max_number_scraper(html: str) -> int:
    """
    XPATH: XPath /html/body/div[2]/div/div/main/div/div/div[2]/div/div/div[3]/nav/span/span/font/font


    or can be


    XPATH /html/body/div[2]/div/div/main/div/div/div[2]/div/div/div[3]/nav/a[2]/span


    :param html:
    :return:
    """
    bs = BeautifulSoup(html, "lxml")
    nav = bs.find("nav", attrs={"aria-label": "Paginare"})
    if not nav:
        raise IOError
    # main = bs.find("main")
    # if not main:
    #     raise IOError
    # # For traceback path
    # div1 = bs.find("div")
    # if not div1:
    #     raise IOError
    # div2 = bs.find("div")
    # if not div2:
    #     raise IOError
    # div3 = bs.find_all("div")[2]
    # if not div3:
    #     raise IOError
    # div4 = bs.find("div")
    # if not div4:
    #     raise IOError
    # div5 = bs.find("div")
    # if not div5:
    #     raise IOError
    # div6 = bs.find_all("div")[3]
    # if not div6:
    #     raise IOError
    # nav = bs.find("nav")
    # if not nav:
    #     raise IOError
    pagination_elements = nav.find_all("a")
    if not pagination_elements:
        pagination_number_max = 1
        return pagination_number_max

    pagination_number_max = int(pagination_elements[-2].text)
    return pagination_number_max


imobiliare_download_html_home_offers = DownloadHtmlHomeOffersService(
        domain_url="https://www.imobiliare.ro",
        url_list="https://www.imobiliare.ro/inchirieri-apartamente/bucuresti/2-camere?amenities=air-conditioning&nearby=metro-station&price=0-400",
        name="imobiliare",
        pagination_number_max_scraper=pagination_max_number_scraper
    )


if __name__ == "__main__":
    asyncio.run(imobiliare_download_html_home_offers.save_session())