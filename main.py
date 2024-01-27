from telegram.ext import CommandHandler, MessageHandler, filters

from logs.mylogging import time_log_decorator

from handlers import user
from handlers import admin
from handlers import data_erasure
from handlers import support

from settings.background_objects import launch_all_background_stuff
from settings.app import application


@time_log_decorator
def telegram_bot(application):
    user_command_handler_functions = [
        user.start,
        user.pause,
        user.template,
        user.add,
        user.searches,
        user.delete,
        support.support,
        user.help,
    ]

    admin_command_handler_functions = [
        admin.ban,
        admin.unban,
        admin.mail_user,
        admin.mail_all_users,
        admin.support_on,
        admin.support_off,
        admin.get_bot_status,
        admin.bot_down,
        admin.bot_up_notification,
        admin.admin,
    ]

    command_handler_functions = (
        user_command_handler_functions + admin_command_handler_functions
    )

    message_handler_functions = [
    ]

    other_handlers = [
        data_erasure.forget_me_conv_handler,
        support.support_pic_handler,
    ]

    application.add_error_handler(user.error)

    for handler in other_handlers:
        application.add_handler(
            handler
        )  # add conversation handlers before message handlers!

    for function in message_handler_functions:
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, function)
        )

    for function in command_handler_functions:
        application.add_handler(CommandHandler(f"{function.__name__}", function))

    application.run_polling()


if __name__ == "__main__":
    launch_all_background_stuff()
    telegram_bot(application)
