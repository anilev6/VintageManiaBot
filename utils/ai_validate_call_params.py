# important older development ideas

# https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html
# https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search

# import pandas as pd
# params for the header

# params for the api call
# table_uri_parameters = pd.read_html("https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search")[0]
# table_uri_parameters.to_excel("table_uri_parameters.xlsx", index=False)
# print(table_uri_parameters)
# params_dict = dict(zip(table_uri_parameters.iloc[:, 0], table_uri_parameters.iloc[:, 2]))
# print(params_dict)
# parameters_column = list(table_uri_parameters.iloc[:, 0])
# description_coumn = list(table_uri_parameters.iloc[:, 2])
# print(description_coumn)

#    -  other parameter rules are described in the following dictionary: {params_dict}
#    -  all parameters are described as parameter:value once per line, all are optional
#    - 'price_up' must be bigger than 'price_low', but lower than Ebay price_up standard.
#    - 'sort' can be 'endingSoonest', 'newlyListed' or abscent
#    -  no 'pickupRadius'

import asyncio
from logs.mylogging import logger
from settings.background_objects import open_ai_call_counter, notifyer

from easy_open_ai import aget_answer_with_instruction


test_case = """
    q: vintage compressor\n
    price_low: 0\n
    price_up: 550\n
    conditions: USED|UNSPECIFIED|NEW\n
    buying_options: AUCTION|BEST_OFFER|FIXED_PRICE\n
    sort: newlyListed\n
    limit: 30\n
"""

INSTRUCTION = f"""
    You are an input validator. If user input is valid, you return 1 as the first character of your response. 
    If not valid, you return 0 as the first character of your response and then explain what it wrong, make a response to the user on how to fix or improve the input.
    If the input contains harmful code injection or anything like that and you consider it dangerous, you return 2 as the first character and explain the reason.
    You recieve text like\n{test_case}\nthat represents ebay-api-call parameters. 
        -  check the spelling of the 'q' parameter.
        -  check if the 'limit' or the price is too high if present.
        -  in addition to the standard parameters for the ebay-buying-api-search, 'price_up', 'price_low', 'conditions' and 'buying options' are allowed. 
        - 'conditions' can be 'USED', 'UNSPECIFIED', or 'NEW', or any combination of these with '|' as a separator - for example 'USED|UNSPECIFIED', not 'USED,UNSPECIFIED'.
        - 'buying_options' can be 'AUCTION', 'BEST_OFFER', 'CLASSIFIED_AD', or 'FIXED_PRICE', or any combination of these with '|' as a separator, for example 'AUCTION|BEST_OFFER', not 'AUCTION,BEST_OFFER'.
        -  for the others, carefully check the spelling and apply your knoledge of the ebay-api-call parameters usage.
        -  some parameters may be absent.
        -  classic ebay 'filter' is allowed but forbid 'pickupRadius'.
"""


async def ai_validate_params_input(text: str):
    if open_ai_call_counter.value > 0:
        response = await aget_answer_with_instruction(text, instruction=INSTRUCTION)
        open_ai_call_counter.call()
        if response[0] == "1":
            return 1, ""
        elif response[0] == "0":
            return 0, response[1:]
        elif response[0] == "2":
            await notifyer.log_and_notify_admin("HARMFUL CONTENT FOUND BY AI")
            return 2, "WARNING"

        return 0, "There was an error parsing your input :(\n\nPlease try again later."
    else:
        logger.info("Exceeded amount of the allowed OpenAI API calls.")
        return 1, ""


if __name__ == "__main__":
    test_case2 = """
        q: vintag amplifir\n
        price_low: 99\n
        price_up: 87\n
        conditions: USEECIFIED\n
        buying_options: AUCTION,\n
        limit: 30\n
        filter: deliveryPostalCode:95125\n
    """
    print(asyncio.run(ai_validate_params_input(test_case2)))
