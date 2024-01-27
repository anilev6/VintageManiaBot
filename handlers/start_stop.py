import asyncio

from logs.mylogging import logger
from settings import background_tasks
from settings import background_objects


# ---------------------------------------------------------ON START/SHUTDOWN--------------------------------------------------------
async def notify_all_users(application, text):
    # notify the users on startup / does not work
    # user_data = application.user_data # this does not see present user_data for some reason
    # if user_data:
    #     await asyncio.gather(*[application.bot.send_message(chat_id=tg_id, text=text, parse_mode='MarkDownV2') for tg_id in user_data.keys()])
    pass


async def on_startup_async(application):
    await asyncio.sleep(63)
    NOTIFICATION = "🍑 *The bot is up again!*\n\n_to resume posting_ /pause _\+_ /start"
    await notify_all_users(application, NOTIFICATION)
    logger.info("USERS NOTIFIED ON START")


async def on_shutdown_async(application):
    NOTIFICATION = "😴 *The bot is down\.*"
    await notify_all_users(application, NOTIFICATION)
    logger.info("USERS NOTIFIED ON SHUTDOWN")


def on_startup(application):
    background_objects.launch_all_background_stuff()
    background_tasks.run_background_task(
        "notify_users_bot_start", on_startup_async, application
    )


def on_shutdown(application):
    background_tasks.stop_all_background_tasks()
    background_tasks.run_background_task(
        "notify_users_bot_shutdown", on_shutdown_async, application
    )
