import logging
import re
from scrapy import Request
from w3lib.url import canonicalize_url, url_query_cleaner

from scrapy.http import FormRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..items import ProductItem, ProductItemLoader

logger = logging.getLogger(__name__)


def load_product(response):
    """Load a ProductItem from the product page response."""
    loader = ProductItemLoader(item=ProductItem(), response=response)

    # Clean and canonicalize the URL before adding it to the loader
    url = url_query_cleaner(response.url, ["snr"], remove=True)
    url = canonicalize_url(url)
    loader.add_value("url", url)

    # Extract the ID from the URL and construct the reviews URL
    found_id = re.findall("/app/(.*?)/", response.url)
    if found_id:
        id = found_id[0]
        reviews_url = (
            f"http://steamcommunity.com/app/{id}/reviews/?browsefilter=mostrecent&p=1"
        )
        loader.add_value("reviews_url", reviews_url)
        loader.add_value("id", id)

    # Extract publication details from the response
    details = response.css(".details_block").extract_first()
    try:
        details = details.split("<br>")
        details = [re.sub("<[^<]+?>", "", line) for line in details]
        details = [re.sub("[\r\t\n]", "", line).strip() for line in details]
        for item in details:
            match = re.match(r"([^:]+):\s*(.*)", item)
            if match:
                key, value = match.groups()

                # Separate the values for 'Developer,' 'Publisher,' and 'Release Date'
                if key.lower() == "developer":
                    developer = re.search(r"(.*?)Publisher:", value).group(1).strip()
                    print(developer)
                    publisher = (
                        re.search(r"Publisher:(.*?)Release Date:", value)
                        .group(1)
                        .strip()
                    )
                    release_date = (
                        re.search(r"Release Date:(.*)", value).group(1).strip()
                    )
                    print(release_date)
                    loader.add_value("developer", developer)
                    loader.add_value("publisher", publisher)
                    loader.add_value("release_date", release_date)
                else:
                    loader.add_value(key.lower(), value.strip())

    except Exception as e:  # Handle exceptions more specifically
        logger.error(f"Error processing publication details: {e}")

    # Load various product information using CSS selectors and XPaths
    loader.add_css("app_name", ".apphub_AppName ::text")
    loader.add_css("specs", ".game_area_details_specs a ::text")
    loader.add_css("tags", "a.app_tag::text")

    price = response.css(".game_purchase_price ::text").extract_first()
    if not price:
        price = response.css(".discount_original_price ::text").extract_first()
        loader.add_css("discount_price", ".discount_final_price ::text")
    loader.add_value("price", price)

    sentiment = (
        response.css(".game_review_summary")
        .xpath('../*[@itemprop="description"]/text()')
        .extract()
    )
    # If there is a digit in the sentiment, then there isn't not enough reviews to determine sentiment.
    if filter(str.isdigit, sentiment):
        sentiment = "Not enough reviews to determine sentiment."
        loader.add_value("sentiment", sentiment)
    else:
        loader.add_value("sentiment", sentiment)
    loader.add_css("n_reviews", ".responsive_hidden", re="\(([\d,]+) reviews\)")

    loader.add_xpath(
        "metascore",
        '//div[@id="game_area_metascore"]/div[contains(@class, "score")]/text()',
    )

    early_access = response.css(".early_access_header")
    loader.add_value("early_access", bool(early_access))

    return loader.load_item()


class Gamespider(CrawlSpider):
    name = "games"
    start_urls = ["http://store.steampowered.com/search/?sort_by=Released_DESC"]

    allowed_domains = ["steampowered.com"]

    rules = [
        # Rule to follow links to individual product pages and call parse_product
        Rule(
            LinkExtractor(allow="/app/(.+)/", restrict_css="#search_result_container"),
            callback="parse_product",
        ),
        # Rule to follow pagination links and continue scraping
        Rule(
            LinkExtractor(allow="page=(\d+)", restrict_css=".search_pagination_right")
        ),
    ]

    def __init__(self, steam_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.steam_id = steam_id

    def start_requests(self):
        # If steam_id is provided, start scraping from the specified product page
        if self.steam_id:
            yield Request(
                f"http://store.steampowered.com/app/{self.steam_id}/",
                callback=self.parse_product,
            )
        else:
            # Otherwise, start scraping from the initial search page
            yield from super().start_requests()

    def parse_product(self, response):
        # Circumvent age selection form.
        if "/agecheck/app" in response.url:
            logger.debug(f"Form-type age check triggered for {response.url}.")

            form = response.css("#agegate_box form")

            action = form.xpath("@action").extract_first()
            name = form.xpath("input/@name").extract_first()
            value = form.xpath("input/@value").extract_first()

            formdata = {name: value, "ageDay": "1", "ageMonth": "1", "ageYear": "1955"}

            # Submit a form request to handle age verification
            yield FormRequest(
                url=action,
                method="POST",
                formdata=formdata,
                callback=self.parse_product,
            )

        else:
            # If no age check form is encountered, yield the loaded product
            yield load_product(response)
