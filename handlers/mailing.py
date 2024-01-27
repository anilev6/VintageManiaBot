from telegram import Update
from telegram.ext import CallbackContext

import asyncio
from datetime import datetime
from random import randint, shuffle

from logs.mylogging import redacted
from settings.settings import QUEUE_TIME_INERVAL
from settings.background_tasks import run_background_task, stop_background_task
from settings.background_objects import ebay_call_counter, notifyer

from ebay.ebay_call import get_ebay_search_result, parse_ebay_search_output


# ----------------------------------MAILING USERS-------------------------------------------
def start_mailing_task(update: Update, context: CallbackContext):
    amount_of_searches = len([k for k in context.user_data.keys() if k.isdigit()])
    if amount_of_searches > 0:
        user_id = str(update.message.from_user.id)  # a unique name for a task
        run_background_task(user_id, mailing, update, context)


def stop_mailing_task(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    stop_background_task(user_id)


async def mailing(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    while context.user_data["status"] == "on":
        results = await call_ebay(update, context)
        if results:
            context.user_data["last_mailed"] = datetime.now()
            cache = context.bot_data.get("cache")
            if not cache:
                context.bot_data["cache"] = {}
            for i in parse_ebay_search_output(
                results, user_id, cache=context.bot_data["cache"]
            ):
                await update.message.reply_text(i, parse_mode="MarkDownV2")
                await asyncio.sleep(randint(3, 9))
        await asyncio.sleep(QUEUE_TIME_INERVAL)


async def call_ebay(update: Update, context: CallbackContext) -> list:
    user_id = str(update.message.from_user.id)
    results = []
    for k, v in dict(context.user_data).items():
        if k.isdigit():  # the convention is searches stored as a number
            if ebay_call_counter.value <= 0:
                await notifyer.log_and_notify_admin(
                    "Exceeded amount of the allowed eBay API calls.", once=True
                )
                break
            raw_result = await get_ebay_search_result(dict(v))
            if type(raw_result) == list:
                results += raw_result
            else:
                notification = f"user {user_id} - {raw_result}"
                await update.message.reply_text(redacted(raw_result))
                await notifyer.log_and_notify_admin(notification, once=True)
                break
    shuffle(results)
    return results
