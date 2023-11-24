BOT_NAME = "steam"

SPIDER_MODULES = ["steam.spiders"]
NEWSPIDER_MODULE = "steam.spiders"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"

ROBOTSTXT_OBEY = True

DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.redirect.RedirectMiddleware": None,
    "steam.middlewares.CircumventAgeCheckMiddleware": 600,
}

CONCURRENT_REQUESTS = 32
AUTOTHROTTLE_ENABLED = True

DUPEFILTER_CLASS = "steam.middlewares.SteamDupeFilter"

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # Never expire.
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [301, 302, 303, 306, 307, 308]
HTTPCACHE_STORAGE = "steam.middlewares.SteamCacheStorage"


FEED_EXPORT_ENCODING = "utf-8"
