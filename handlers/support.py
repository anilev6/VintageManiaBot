from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from telegram.error import TelegramError

from logs.mylogging import logger
from settings import settings
from settings import background_objects

from handlers.user import pause
from handlers.role_check import (
    check_role_decorator,
    is_allowed_user,
    is_registered_user,
    is_active_user,
)

# ----------------------------------------------------CONSTANTS--------------------------------------------------------
SUPPORT_COMMAND = "/support"
MAIL_ALL_USERS_COMMAND = "/mail_all_users"
MAIL_USER_COMMAND = "/mail_user"
ADMIN_NOTIFICATION = "[admin sends to {}]\n\n{}"
SUPPORT_REQUEST = "🍑 Support request from {}\n\n{}"
REQUEST_SUBMITTED_REPLY = "🍑 *Request submitted*\.\n_The answer will be sent here when your request is processed \:\)_"
SUPPORT_UNAVAILABLE_REPLY = "Support is currently unavailable :("
PHOTO_ID_LOG = " pic # {}"


# -----------------------------------------------------HELPERS--------------------------------------------------
async def log_and_reply(update, text, parse_mode=None):
    """Logs the message and sends a reply to the user."""
    logger.info(text)
    try:
        await update.message.reply_text(text, parse_mode=parse_mode)
    except TelegramError as e:
        logger.error(f"Error in sending message: {e}")


async def send_photo_to_users(context, photo_id, text, user_ids):
    """Sends photo to a list of user IDs."""
    for user_id in user_ids:
        try:
            await context.bot.send_photo(chat_id=user_id, caption=text, photo=photo_id)
        except TelegramError as e:
            logger.error(f"Error in sending photo to user {user_id}: {e}")


# ----------------------------------------------------COMMANDS--------------------------------------------------
@check_role_decorator(
    allowed_role_checker_list=[is_allowed_user, is_registered_user, is_active_user]
)
async def support(update: Update, context: CallbackContext):
    if not background_objects.notifyer.on:
        await log_and_reply(update, SUPPORT_UNAVAILABLE_REPLY)
        return

    sender_id = str(update.message.from_user.id)
    text = update.message.text[8:].strip() if update.message.text else ""
    full_text = SUPPORT_REQUEST.format(sender_id, text)

    if text:
        await pause(update, context)
        await background_objects.notifyer.send(text=full_text, once=True)
        await log_and_reply(update, REQUEST_SUBMITTED_REPLY, parse_mode="MarkDownV2")


# Picture support and sending
@check_role_decorator(
    allowed_role_checker_list=[is_allowed_user, is_registered_user, is_active_user]
)
async def photo_handler(update: Update, context: CallbackContext):
    sender_id = str(update.message.from_user.id)
    caption = update.message.caption
    photo_id = update.message.photo[-1].file_id if update.message.photo else None

    if sender_id in settings.ADMIN_GROUP:
        if caption:
            if MAIL_ALL_USERS_COMMAND in caption:
                text = caption.replace(MAIL_ALL_USERS_COMMAND, "").strip()
                active_users = context.bot_data.get("cache", {}).keys()
                await send_photo_to_users(context, photo_id, text, active_users)
                await log_and_reply(update, ADMIN_NOTIFICATION.format("all", text))

            elif MAIL_USER_COMMAND in caption:
                lines = caption.split("\n")
                target_user_id = lines[0].replace(MAIL_USER_COMMAND, "").strip()
                text = "\n".join(lines[1:])
                await send_photo_to_users(context, photo_id, text, [target_user_id])
                await log_and_reply(
                    update, ADMIN_NOTIFICATION.format(target_user_id, text)
                )

    if caption and SUPPORT_COMMAND in caption:
        if not background_objects.notifyer.on:
            await log_and_reply(update, SUPPORT_UNAVAILABLE_REPLY)
            return

        text = caption.replace(SUPPORT_COMMAND, "").strip()
        full_text = SUPPORT_REQUEST.format(sender_id, text)
        await pause(update, context)
        await background_objects.notifyer.send(
            photo_id=photo_id, text=full_text, once=True
        )
        await log_and_reply(update, REQUEST_SUBMITTED_REPLY, parse_mode="MarkDownV2")


# ----------------------------------------------------PIC HANDLER--------------------------------------------------
support_pic_handler = MessageHandler(filters.PHOTO, photo_handler)
