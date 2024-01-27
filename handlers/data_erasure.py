"""USER PANEL"""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)

from settings.background_objects import users_cleaner

from handlers.role_check import is_registered_user
from handlers.user import pause

# --------------------------------------STATEFUL DELETION CONVERSATION HANDLER--------------------------------------------------
# states
CONFIRMATION = 1


async def start_delete(update: Update, context: CallbackContext) -> int:
    if not is_registered_user(update, context):
        return ConversationHandler.END

    await pause(update, context)
    await update.message.reply_text(
        "*Are you sure you want to delete all your data\?*\nPlease confirm by *'Yes'* or *'No'*\.",
        reply_markup=ReplyKeyboardMarkup(
            [["Yes", "No"]], one_time_keyboard=True, resize_keyboard=True
        ),
        parse_mode="MarkDownV2",
    )

    return CONFIRMATION


async def confirm_delete(update: Update, context: CallbackContext) -> int:
    user_response = update.message.text

    if user_response.lower() == "yes":
        # clear user-data storage; logs automatically rotate;
        # context.user_data.clear() does not remove from the storage

        # manually clean from my storage
        user_id = update.message.from_user.id
        users_cleaner.erase_user(user_id)

        # Send a confirmation message to the user
        await update.message.reply_text(
            "*Your personal data has been successfully deleted*\.\n_Note that deleting info from the logs may take some time\._\n\n*Bye\!*",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="MarkDownV2",
        )

    else:
        await update.message.reply_text(
            "Data deletion cancelled.", reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END


# Handler for canceling the operation
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Operation cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


forget_me_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("forget_me", start_delete)],
    states={
        CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
