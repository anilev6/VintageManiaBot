from mongopersistence import MongoPersistence
from telegram.ext import ApplicationBuilder

from settings.settings import MONGO_URL, TG_BOT_TOKEN

# from ..handlers.start_stop import on_startup, on_shutdown


# -------------------------------------------TELEGRAM BOT DB------------------------------
persistence = MongoPersistence(
    mongo_url=MONGO_URL,
    db_name="vintage-mania-database",
    name_col_user_data="user-data-collection",
    name_col_bot_data="bot-data-collection",
    create_col_if_not_exist=True,
    # ignore_general_data=["cache"],
    # ignore_user_data=["foo", "bar"],
    load_on_flush=False,
    update_interval=60,
)

# --------------------------------------------TELEGRAM APP---------------------------------
application = (
    ApplicationBuilder()
    .token(TG_BOT_TOKEN)
    .persistence(persistence)
    # .post_init(on_startup) # these cause errors in notifiction sending!
    # .post_shutdown(on_shutdown) # both sync and async funcs don't work
    .build()
)
