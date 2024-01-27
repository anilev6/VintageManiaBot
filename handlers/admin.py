"""ADMIN PANEL"""
from telegram import Update
from telegram.ext import CallbackContext

import asyncio
from datetime import datetime
import time
from textwrap import dedent

from settings import settings
from settings.background_tasks import task_storage, stop_all_background_tasks
from settings.background_objects import (
    notifyer,
    ebay_call_counter,
    open_ai_call_counter,
)
from settings.app import application

from handlers.role_check import check_role_decorator, is_user_admin, is_allowed_user


# ----------------------------------------------COMMANDS-----------------------------------------------------
@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def ban(update: Update, context: CallbackContext):
    message_text = update.message.text
    user_id = message_text[4:].strip()
    if user_id == settings.MY_TG_ID:
        return
    banned_users = context.bot_data.get("banned_users")
    if not banned_users:
        context.bot_data["banned_users"] = []
    context.bot_data["banned_users"].append(user_id)
    await notifyer.log_and_notify_admin(f"user {user_id} banned")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def unban(update: Update, context: CallbackContext):
    message_text = update.message.text
    user_id = message_text[6:].strip()
    banned_users = context.bot_data.get("banned_users")
    if not banned_users:
        return
    if user_id not in context.bot_data["banned_users"]:
        return
    context.bot_data["banned_users"].remove(user_id)
    await notifyer.log_and_notify_admin(f"user {user_id} unbanned")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def mail_user(update: Update, context: CallbackContext):
    message_to = update.message.text[10:].split("\n")[0].strip()
    message_what = "\n".join(update.message.text.split("\n")[1:])
    await context.bot.send_message(chat_id=message_to, text=message_what)
    await notifyer.log_and_notify_admin(f"Admin message delivered")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def mail_all_users(update: Update, context: CallbackContext):
    message_text = update.message.text[15:].strip()
    for k in context.bot_data.get("cache", {}).keys():
        await context.bot.send_message(chat_id=k, text=message_text)
    await notifyer.log_and_notify_admin(f"Admin message sent to all active users")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def support_on(update: Update, context: CallbackContext):
    if not notifyer.on:
        notifyer.background_refresher_on()
        await notifyer.log_and_notify_admin(f"SUPPORT ACTIVATED")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def support_off(update: Update, context: CallbackContext):
    if notifyer.on:
        await notifyer.log_and_notify_admin(f"SUPPORT DEACTIVATED")
        notifyer.background_refresher_off()


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def get_bot_status(update: Update, context: CallbackContext):
    TEXT = dedent(
        f"""
        {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n
        EBAY API-CALLS TODAY: {ebay_call_counter.calls_today()}
        OPENAI API-CALLS TODAY: {open_ai_call_counter.calls_today()}

        ACTIVE TASKS: {len(task_storage)} - {', '.join(task_storage.keys())}
        ACTIVE USERS: {len(application.bot_data.get('cache',{}))}

        SUPPORT ON: {notifyer.on}
        """
    )
    await update.message.reply_text(TEXT)


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def bot_down(update: Update, context: CallbackContext):
    await notifyer.log_and_notify_admin(f"Urgent app stop by admin via the command.")

    stop_all_background_tasks()
    time.sleep(62)  # time to save a database
    await notifyer.notify_on_shutdown()

    application.stop_running()
    await asyncio.sleep(45)  # time to stop running
    return await application.shutdown()


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def bot_up_notification(update: Update, context: CallbackContext):
    await notifyer.notify_on_restart()


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_user_admin])
async def admin(update: Update, context: CallbackContext):
    TEXT = dedent(
        """
        🍑ADMIN PANEL🍑\n
        /ban _user_id_ 
        /unban _user_id_ 
        /mail_user _user_id_\\n _text_
        /mail_all_users\\n _text_ - mails all active users
        /support_on 
        /support_off
        /get_bot_status  
        /bot_down - urgent bot shutdown  
        /bot_up_notification - notify all active users  
        /admin - menu  
        """
    )
    await update.message.reply_text(TEXT)
