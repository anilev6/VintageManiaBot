from settings.background_tasks import CounterDown, EbayToken, NotifyAdminTG, CleanUsers

from settings.settings import MAX_EBAY_API_CALLS, MAX_OPENAI_API_CALLS
from settings.app import application

# -------- Tasks on the back managers : BackgroundRefresher children -----------------------------------

# data on my server
ebay_call_counter = CounterDown("EBAY", MAX_EBAY_API_CALLS) # counts ebay calls per day
open_ai_call_counter = CounterDown("OPENAI", MAX_OPENAI_API_CALLS) # same for openai
refreshing_ebay_token = EbayToken() # refreshes ebay access token

# works with the app database or requires app
notifyer = NotifyAdminTG(application) # can cache messages sent to the admin group
users_cleaner = CleanUsers(application) # cleans unactive users once in a while

# my app components other than telegram
background_stuff = [
    ebay_call_counter,
    open_ai_call_counter,
    refreshing_ebay_token,
    notifyer,
    users_cleaner,
]

def launch_all_background_stuff():
    for thing in background_stuff:
        thing.background_refresher_on()
