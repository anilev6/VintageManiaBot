# https://developer.ebay.com/api-docs/static/rest-request-components.html#marketpl
# https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
import aiohttp
import asyncio

from settings.settings import DEFAULT_CALL_PARAMS, MAX_CACHE_LEN
from settings.background_objects import (
    ebay_call_counter,
    refreshing_ebay_token,
)
from utils.helpers import textify_search_item


# -----------------------------------------------------------------HELPERS------------------------------------------------------
def pop_or_default(params, key):
    return params.pop(key, DEFAULT_CALL_PARAMS[key])


def user_data_params_to_actual(params):
    if params.get("filter"):
        return params

    filter_line = (
        f"price:[{pop_or_default(params, 'price_low')}..{pop_or_default(params, 'price_up')}],priceCurrency:USD,conditions:{{{pop_or_default(params,'conditions')}}},buyingOptions:{{{pop_or_default(params, 'buying_options')}}}",
    )
    params["filter"] = filter_line
    return params


# -----------------------------------------------------------------GET RAW RESULT------------------------------------------------
async def get_ebay_search_result(params: dict):
    endpoint = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {refreshing_ebay_token.value}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            endpoint, headers=headers, params=user_data_params_to_actual(params)
        ) as response:
            result = await response.json()
            ebay_call_counter.call()

            if not result.get("itemSummaries"):
                return f"Error occurred: {result}"

            return result.get("itemSummaries")  # returns a list if all is ok


# -----------------------------------------------------------------PARSE THE RESULT------------------------------------------------
def parse_ebay_search_output(input_list, user_id, cache: dict = {}):
    """yilds ready to send text"""
    if not cache.get(user_id):
        cache[user_id] = []
    for sr in input_list:
        item_id = sr.get("legacyItemId", "")
        if item_id not in cache[user_id]:
            cache[user_id] = [item_id] + cache[user_id]
            if len(cache[user_id]) > MAX_CACHE_LEN:
                cache[user_id].pop()
            yield textify_search_item(sr)


# -----------------------------------------------------------------SEE HOW IT WORKS------------------------------------------------
async def test():
    parameters = {"q": "vintage compressor", "limit": 5}
    results = await get_ebay_search_result(parameters)
    for i in parse_ebay_search_output(results, 1):
        print(i)


if __name__ == "__main__":
    asyncio.run(test())
