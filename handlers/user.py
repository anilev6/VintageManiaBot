from telegram import Update
from telegram.ext import CallbackContext

import asyncio
from textwrap import dedent

from logs.mylogging import logger
from settings.settings import (
    MAX_USERS_AMOUNT,
    MAX_SEARCHES_AMOUNT,
    DEFAULT_CALL_PARAMS,
    DEFAULT_CALL_PARAMS2,
)

from utils.helpers import (
    escape_markdown_v2,
    params_input_validator,
    params_to_template,
    next_available_search_num,
    extract_digit_from_command,
)

from handlers.role_check import (
    check_role_decorator,
    is_allowed_user,
    is_registered_user,
)
from handlers.mailing import start_mailing_task, stop_mailing_task


# ----------------------------------ERROR HANDLING------------------------------------
async def error(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "An error occurred while processing your request :("
    )
    # Error handling moved to check_role_decorator


# -----------------------------------BOT COMMANDS--------------------------------------
@check_role_decorator(allowed_role_checker_list=[is_allowed_user])
async def start(update: Update, context: CallbackContext):
    user_data = context.user_data
    status = user_data.get("status")

    if not status:
        await handle_new_user(update, context)

    elif status == "on":
        await update.message.reply_text("It's on.")

    elif status == "off":
        start_mailing_task(update, context)
        user_data["status"] = "on"
        await update.message.reply_text("🍑 Posting resumed... ")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_registered_user])
async def pause(update: Update, context: CallbackContext):
    status = context.user_data["status"]
    if status == "on":
        stop_mailing_task(update, context)
        context.user_data["status"] = "off"
        await update.message.reply_text(
            "🍑 Posting paused... \n\nto continue /start\nto /help "
        )


# -----------------------------------------HELPERS----------------------------------------
def get_user_full_info(user) -> dict:
    # Gather user info from telegram user object
    user_info = {
        "user_id": f"{user.id}",
        "username": f"@{user.username}" if user.username else "None",
        "first_name": f"{user.first_name}" if user.first_name else "None",
        "last_name": f"{user.last_name}" if user.last_name else "None",
        "language": f"{user.language_code}" if user.language_code else "None",
    }
    return user_info


async def handle_new_user(update: Update, context: CallbackContext):
    if len(context.bot_data.get("cache", {})) >= MAX_USERS_AMOUNT:
        await update.message.reply_text("Too many users! Sorry :(")
        return

    user_data = context.user_data
    user_data["info"] = get_user_full_info(update.effective_user)
    user_data["1"] = DEFAULT_CALL_PARAMS
    user_data["status"] = "on"

    await send_welcome_message(update)
    start_mailing_task(update, context)


async def send_welcome_message(update: Update):
    welcome_text = dedent(
        """
        *Welcome* 🍑
        
        Here are some commands FYI\:\n

        /start \- mailing on
        /pause \- mailing off
        /help \- see command menu
        
        *Enjoy the Ebay feed* 🍑
    """
    )
    await update.message.reply_text(welcome_text, parse_mode="MarkDownV2")
    await asyncio.sleep(3)


async def save_search(
    update: Update, context: CallbackContext, text: str, new_search_num: str
):
    params = await params_input_validator(
        text
    )  # returns a string if something is wrong
    if type(params) == dict:
        if not params:
            await update.message.reply_text(f"For correct command usage /help")
            return
        if params in context.user_data.values():
            await update.message.reply_text(f"This search already exists")
            return
        context.user_data[new_search_num] = params
        await update.message.reply_text(
            f"🍑 Successfully added\! \n\n№ *{new_search_num}*\n{escape_markdown_v2(params_to_template(params))}\n\n/searches\n/start",
            parse_mode="MarkDownV2",
        )
        return

    elif type(params) == str:
        await update.message.reply_text(
            escape_markdown_v2(params), parse_mode="MarkDownV2"
        )
        return
    logger.warning(f"UNEXPECTED TYPE FROM DICT_VALIDATOR {params}")


# ----------------------------------------------------------OTHER COMMANDS------------------------------------
@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_registered_user])
async def add(update: Update, context: CallbackContext):
    await pause(update, context)

    new_search_num = str(next_available_search_num(context.user_data))

    if new_search_num == "0":
        await update.message.reply_text(
            f":( \n\nExceeded max number of searches: {MAX_SEARCHES_AMOUNT} \n\nTry editing or deleting a search /help"
        )
        return

    text = update.message.text
    await update.message.reply_text(f"Processing your input...")
    await save_search(update, context, text, new_search_num)


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_registered_user])
async def delete(update: Update, context: CallbackContext):
    await pause(update, context)
    text = update.message.text
    text_lines = text.split("\n")
    search_num = str(extract_digit_from_command(text_lines[0]))
    if search_num not in context.user_data.keys():
        await update.message.reply_text(
            f"No such search: {search_num}\n\nFor correct command usage /help"
        )
        return

    search = context.user_data.pop(search_num)
    await update.message.reply_text(
        f"🍑 № *{search_num}* successfully deleted\!\n\n/searches\n/start",
        parse_mode="MarkDownV2",
    )


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_registered_user])
async def searches(update: Update, context: CallbackContext):
    await pause(update, context)
    for search_num in context.user_data.keys():
        if search_num.isdigit():
            await update.message.reply_text(
                f"🍑 № *{search_num}*\n{escape_markdown_v2(params_to_template(context.user_data[search_num]))}",
                parse_mode="MarkDownV2",
            )


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_registered_user])
async def template(update: Update, context: CallbackContext):
    await pause(update, context)
    await update.message.reply_text(f"🍑 To learn the command try the following:")
    await update.message.reply_text(f"/add\n{params_to_template(DEFAULT_CALL_PARAMS2)}")


@check_role_decorator(allowed_role_checker_list=[is_allowed_user, is_registered_user])
async def help(update: Update, context: CallbackContext):
    await pause(update, context)
    TEXT = dedent(
        f"""
        {escape_markdown_v2('------------------------------------------MENU------------------------------------------')}\n
        /start \- mailing on
        /pause \- mailing off
        /searches \- see all your current searches
        /template \- an extended example for your search
        /add
            q\: vintage car
            price\_up\: 2000
                    \- add a search
        /delete \__number of the search_\_ 
                    \- delete a search
        /support \__your request here_\_ 
                    \- leave feedback and/or report a problem; 
                    \- accepts pictures \(the command has to be in the caption\);  
        /help \- all available commands
        /forget\_me \- deletes all of your personal data forever 
        """
    )
    await update.message.reply_text(TEXT, parse_mode="MarkDownV2")
