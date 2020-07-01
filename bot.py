import logging
import io

import pytz
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import youtube_data as ytd
import user
from user import User, UserState

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start_command(update, context):
    """Send a message when the command /start is issued."""
    user = User.load(update.effective_user.id)

    message = (
        f"Hi {update.effective_user.name} 😊\n"
        "YouTube saves a lot of data about you, however I can help you to "
        "get some insight into this data. So for me the help you, you need to "
        "download your data and send me the files `watch-history.json` and "
        "`search-history.json`.\n\n"
        "Some of the graphs I can create are time-sensetive, so it is "
        "important that I know in which timezone you live in. At the moment I "
        f"think/asume you live in `{user.timezone}`, if this is wrong you "
        "can correct me with the /timezone command.\n\n"
        "*Disclaimer:* This is not an official YouTube application, nor am I "
        "[flofriday](https://github.com/flofriday), in any way "
        "associated with YouTube or Google."
    )

    update.message.reply_text(
        message, parse_mode="Markdown", disable_web_page_preview=True
    )


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Help!")


def info_command(update, context):
    user = User.load(update.effective_user.id)
    message = (
        f"State: {UserState(user.state).name}\nTimezone: {user.timezone}\n"
        f"Number of anaylyzes: {user.analyzes}"
    )
    update.message.reply_text(message, disable_web_page_preview=True)


def timezone_command(update, context):
    """Set the timezone for the user"""
    user = User.load(update.effective_user.id)
    user.state = UserState.send_timezone
    user.update()

    message = (
        "Send me the timezone you live in.\n"
        "Unfortunatly, I am very strict about the format 😅.\n"
        "The format must be like `Europe/Vienna`.\n"
        "Here is the [Wikipedia Link]"
        "(https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) "
        "to help you out."
    )
    update.message.reply_text(
        message, parse_mode="Markdown", disable_web_page_preview=True
    )


def document_message(update, context):
    """React to files the user sends the bot"""

    filename = update.message.document.file_name
    if filename == "search-history.json":
        analyze_search(update, context)
        return
    elif filename == "watch-history.json":
        return

    message = (
        "Sorry, the file must either be named `search-history.json` or "
        "`watch-history.json`. 😔"
    )
    update.message.reply_text(
        message, parse_mode="Markdown", disable_web_page_preview=True
    )


def text_message(update, context):
    """Handle normal messages"""

    user = User.load(update.effective_user.id)
    if user.state == UserState.send_timezone:
        if update.message.text not in pytz.all_timezones:
            update.message.reply_text("Sorry, I don't know that timezone. 😰")
            return
        user.timezone = update.message.text
        user.state = UserState.idle
        user.update()
        update.message.reply_text("Great, set your new timezone. 😄")
        return

    # I don't know what else to do
    update.message.reply_text("Sorry, I don't know what you want. 😔")


def unknown_message(update, context):
    update.message.reply_text("Sorry, I don't know what you want. 😔")


def analyze_search(update, context):
    document = update.message.document
    f = None
    try:
        f = document.get_file(30)
    except:
        update.message.reply_text(
            "An error occoured while downloading your file."
        )
        return

    # Load the user and the data into a dataframe
    user = User.load(update.effective_user.id)
    json = f.download_as_bytearray().decode("utf-8")
    df = ytd.load_search_history(json, user.timezone)

    # Overall information about the searches
    info_message = (
        f"Searches since {df['time'].min().strftime('%b %d %Y')}: "
        f"*{len(df)}*\n"
        f"Average searches per day: "
        f"*{len(df)/((df['time'].max()-df['time'].min()).days):.2f}*"
    )
    update.message.reply_text(info_message, parse_mode="Markdown")

    # Plot the words used most often
    plt1 = ytd.searchword_plot(df, 24)
    fig1 = plt1.get_figure()
    fig1.tight_layout()
    image1 = io.BytesIO()
    fig1.savefig(image1, format="png", dpi=300)
    image1.seek(0)
    context.bot.send_photo(
        chat_id=user.telegram_id, photo=image1,
    )

    # Plot the search activity over time
    plt1 = ytd.search_timeline_plot(df)
    fig1 = plt1.get_figure()
    fig1.tight_layout()
    image1 = io.BytesIO()
    fig1.savefig(image1, format="png", dpi=300)
    image1.seek(0)
    context.bot.send_photo(
        chat_id=user.telegram_id, photo=image1,
    )

    # Update the counter for the user
    user.analyzes += 1
    user.update()
    update.message.reply_text("Done 😊", parse_mode="Markdown")


def main():
    """Start the bot."""

    # Initialize the database
    user.__init__("bot.db")

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(
        "914981447:AAGETT1C0EAZ0yXsqGtEp7hymlBlGrbH3rs", use_context=True
    )
    print("Bot running...")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("timezone", timezone_command))
    dp.add_handler(CommandHandler("info", info_command))
    dp.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, text_message))
    dp.add_handler(MessageHandler(Filters.document, document_message))
    dp.add_handler(MessageHandler(Filters.all, unknown_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
