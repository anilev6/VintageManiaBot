import os


def get_secret_by_name(name: str):
    return os.getenv(name)


# MongoDB
MONGO_URL = get_secret_by_name("MONGO_URL")
MAX_CACHE_LEN = 500  # cache len per user; stored in bot_data

# Ebay creds
ENCODED_CREDENTIALS = get_secret_by_name("ENCODED_CREDENTIALS")

# TG creds
TG_BOT_TOKEN = get_secret_by_name("TG_BOT_TOKEN")
MY_TG_ID = str(get_secret_by_name("MY_TG_ID"))

ADMIN_GROUP = [MY_TG_ID]

# Mailing settings
MAX_EBAY_API_CALLS = 5000  # default Ebay partners program; buying-api
MAX_OPENAI_API_CALLS = 1000  # my limit
QUEUE_TIME_INERVAL = 3600  # IN SECONDS, 1 hour interval in mailing a user
MAX_SEARCHES_AMOUNT = 8  # one user can have up to 8 searches
MAX_USERS_AMOUNT = int(
    MAX_EBAY_API_CALLS * QUEUE_TIME_INERVAL / (24 * 60 * 60 * MAX_SEARCHES_AMOUNT)
)

DEFAULT_CALL_PARAMS = {
    "q": "vintage compressor",
    "price_low": "0",
    "price_up": "550",
    "conditions": "USED|NEW",
    "buying_options": "AUCTION",
    "sort": "endingSoonest",
    "limit": "15",
}

DEFAULT_CALL_PARAMS2 = {
    "q": "vintage car",
    "price_low": "0",
    "price_up": "550",
    "conditions": "USED|UNSPECIFIED|NEW",
    "buying_options": "AUCTION|BEST_OFFER|FIXED_PRICE|CLASSIFIED_AD",
    "sort": "newlyListed",
    "limit": "15",
}
