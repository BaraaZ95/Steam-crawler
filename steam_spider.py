from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from steam.spiders.games_spider import Gamespider
from steam.spiders.review_spider import ReviewSpider


process = CrawlerProcess(get_project_settings())
process.crawl(Gamespider)
# process.crawl(ReviewSpider) # Uncomment this line if you want to run the reviews crawler
process.start()
