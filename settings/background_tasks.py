import asyncio
from datetime import datetime, timedelta

from logs.mylogging import logger, redacted, time_log_decorator
from . import settings

from ebay import ebay_token


# all app background processes live here
# convention:
# all keys are unique
# user_id:mailing task for my telegram users
# a unique string for others
# telegram runs the loop
task_storage = {}


# ----------------------------------------MAIN OPERATIONS--------------------------------
def stop_all_background_tasks():
    for k in list(task_storage.keys()):  # because otherwise len changes
        stop_background_task(k)
    logger.info(f"All tasks shut down. {len(task_storage)} tasks now")


def stop_background_task(task_name):
    if task_storage.get(task_name):
        previous_task = task_storage.pop(task_name)
        try:
            previous_task.cancel()
            logger.info(f"Task {task_name} is cancelled. {len(task_storage)} tasks now")
        except Exception as e:
            logger.error(f"Error in canceling task {task_name}: {e}")


def task_done_callback(t, task_name):
    try:
        task_storage.pop(task_name)
        logger.info(f"Task {task_name} is done. {len(task_storage)} tasks now")
    except KeyError:
        pass


def run_background_task(task_name, task_func, *func_args, **func_key_args):
    # delete the previous task if present first
    stop_background_task(task_name)
    try:
        loop = asyncio.get_event_loop()
        task = loop.create_task(task_func(*func_args, **func_key_args))
        task.add_done_callback(lambda t: task_done_callback(t, task_name))
        task_storage[task_name] = task
        logger.info(f"Task {task_name} is launched. {len(task_storage)} tasks now")
    except Exception as e:
        logger.error(f"Error in launching task {task_name}: {e}")


# ---------------------------------------USEFUL BACKGROUND STUFF------------------------
class BackgroundRefresher:
    def __init__(self, process_name, refresh_rate_seconds):
        self.process_name = process_name
        self.refresh_rate_seconds = refresh_rate_seconds
        self.on = False  # turn off refresher

    def background_refresher_on(self):
        if not self.on:
            run_background_task(self.process_name, self.refresher)
            self.on = True

    def background_refresher_off(self):
        if self.on:
            stop_background_task(self.process_name)
            self.on = False

    async def refresher(self):
        """BACKGROUND TASK"""
        while self.on:
            # what to refresh
            await asyncio.sleep(self.refresh_rate_seconds)


class EbayToken(BackgroundRefresher):
    def __init__(self):
        self.process_name = "ebay_token_refresher"
        self.refresh_rate_seconds = 60 * 60 * 2
        self.on = False
        self.value = None

    async def refresher(self):
        while self.on:
            try:
                # block all other tasks because important
                result = ebay_token.get_app_token()
                self.value = result["access_token"]
                logger.info("EBAY TOKEN UPDATED")
                self.refresh_rate_seconds = result["expires_in"] - 5
            except Exception as e:
                logger.error(f"ERROR IN EBAY TOKEN UPDATER {redacted(str(e))}")
                raise e
            finally:
                await asyncio.sleep(self.refresh_rate_seconds)


class CounterDown(BackgroundRefresher):
    """COUNT API CALLS PER DAY SUBSTRACTING FROM MAX"""

    def __init__(self, name: str, default_value):
        self.name = name  # api of what - EBAY, OPENAI, etc
        self.process_name = f"{name.lower()}_api_calls_counter_refresher"
        self.refresh_rate_seconds = 24 * 60 * 60  # 1 day
        self.on = False
        self.value = default_value
        self.default_value = default_value

    async def refresher(self):
        while self.on:
            logger.info(f"{self.name} API CALLS TODAY: {self.calls_today()}")
            self.value = self.default_value
            logger.info(f"{self.name} API CALLS COUNTER REFRESHED")
            logger.info(f"{self.name} API CALLS: {self.value}")

            await asyncio.sleep(self.refresh_rate_seconds)

    def calls_today(self):
        return self.default_value - self.value

    def call(self):
        self.value -= 1


class CleanUsers(BackgroundRefresher):
    # https://docs.python-telegram-bot.org/en/v20.7/telegram.ext.application.html#telegram.ext.Application.drop_user_data
    # Fully dropping user_data is problematic for some reason;

    # Apparently, when user_data is being deleted in a bot [context.user_data.clear()],
    # the deletion commit does not reach the actual storage, and the other way around.
    # Thus, we will be handling user data deletion as follows

    def __init__(self, app):
        self.process_name = "inactive_user_cleaner"
        self.refresh_rate_seconds = 4 * 24 * 60 * 60  # 4 days
        self.on = False
        self.app = app

    def erase_user(self, user_id: int):
        self.app.drop_user_data(user_id)
        self.app.bot_data.get("cache", {}).pop(f"{user_id}")
        logger.info(f"User {user_id} removed")

    def clear_unactive_users(self):
        time_now = datetime.now()
        cache = self.app.bot_data.get("cache", {})
        all_users = list(cache.keys())  # my convention
        for user in all_users:
            last_mailed = self.app.user_data.get(user, {}).get("last_mailed")
            if last_mailed and (time_now - last_mailed) >= timedelta(days=7):
                self.erase_user(int(user))

    async def refresher(self):
        while self.on:
            logger.info(f"CLEARING INACTIVE USERS")
            self.clear_unactive_users()
            logger.info(f"INACTIVE USERS CLEARED")
            await asyncio.sleep(self.refresh_rate_seconds)


class NotifyAdminTG(BackgroundRefresher):
    def __init__(self, app):
        self.process_name = "admin_notification_cache_refresher"
        self.refresh_rate_seconds = 60 * 60 * 3
        self.on = False
        self.admin_ids = settings.ADMIN_GROUP
        self.app = app
        self.cache = []  # notifications that shouldn't appear more than once in a while

    async def refresher(self):
        while self.on:
            self.cache = []
            await asyncio.sleep(self.refresh_rate_seconds)

    async def send(
        self, text=None, group=[], photo_id=None, once=False, parse_mode=None
    ):
        if (str(photo_id) in self.cache) or (text in self.cache):
            return

        if not text and not photo_id:
            return

        if not group:
            group = self.admin_ids

        for tg_id in group:
            try:
                if photo_id and text:
                    await self.app.bot.send_photo(
                        chat_id=tg_id, photo=photo_id, caption=text
                    )
                elif photo_id:
                    await self.app.bot.send_photo(chat_id=tg_id, photo=photo_id)

                elif text:
                    await self.app.bot.send_message(
                        chat_id=tg_id, text=text, parse_mode=parse_mode
                    )

            except Exception as e:
                logger.error(f"Failed to send: f{str(e)}")
                return

        if once:
            self.cache.append(text)
            if photo_id:
                self.cache.append(str(photo_id))

    async def log_and_notify_admin(self, text, once=False):
        if text in self.cache:
            return
        logger.info(text)
        await self.send(text=text, once=once)

    async def send_all_active_users(self, text, photo_id=None, parse_mode=None):
        all_active_users = self.app.bot_data.get("cache", {}).keys()
        if all_active_users:
            await self.send(
                text=text,
                group=all_active_users,
                photo_id=photo_id,
                parse_mode=parse_mode,
            )

    async def notify_on_restart(self):
        NOTIFICATION = (
            "🍑 *The bot is up again\!*\n\n_to resume posting_ /pause _\+_ /start"
        )
        await self.send_all_active_users(NOTIFICATION, parse_mode="MarkDownV2")

    async def notify_on_shutdown(self):
        NOTIFICATION = "😴 *The bot is down\.*"
        await self.send_all_active_users(NOTIFICATION, parse_mode="MarkDownV2")
