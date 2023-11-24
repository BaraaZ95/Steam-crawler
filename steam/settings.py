import os

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

FEEDS = {
    "s3://your-bucket-name/output.csv": {
        "format": "csv",
        "overwrite": True,
    },
}
AWS_ACCESS_KEY_ID = "your-access-key"
AWS_SECRET_ACCESS_KEY = "your-secret-key"

# Specify the default output folder
DEFAULT_OUTPUT_FOLDER = "output"


# Define a function to get the output file path based on the spider name
def get_output_file(spider_name):
    return os.path.join(DEFAULT_OUTPUT_FOLDER, f"{spider_name}_output.csv")


# Set the FEED_URI dynamically using the get_output_file function
FEED_URI = get_output_file(os.environ.get("SCRAPY_SPIDER_NAME", "default"))
FEED_FORMAT = "csv"
FEEDS = {
    get_output_file(os.environ.get("SCRAPY_SPIDER_NAME", "default")): {
        "format": "csv",
        "store_empty": False,
        "encoding": "utf8",
        "overwrite": True,  # Set to True if you want to overwrite the file on each run
        "bucket": "your-s3-bucket-name",
        "acl": "private",  # Set the desired ACL
        "region": "your-s3-region",
    }
}
AWS_ACCESS_KEY_ID = "your-access-key"
AWS_SECRET_ACCESS_KEY = "your-secret-key"
