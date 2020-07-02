import logging
import os
import io
import matplotlib
import matplotlib.pyplot as plt

import pytz
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

import youtube_data as ytd
import user
from user import User, UserState

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def send_plot(
    user: User, context, plot: matplotlib.axes.Axes, caption: str = ""
):
    """Send a pandas plot to the specified chat"""
    fig = plot.get_figure()
    fig.tight_layout()
    image = io.BytesIO()
    fig.savefig(image, format="png", dpi=300)
    plt.close(fig)
    image.seek(0)
    context.bot.send_photo(
        chat_id=user.telegram_id,
        photo=image,
        parse_mode="Markdown",
        caption=caption,
    )
    pass


@run_async
def start_command(update, context):
    """Send a message when the command /start is issued."""
    user = User.load(update.effective_user.id)

    # TODO: The guide points nowhere
    message = (
        f"Hi {update.effective_user.name} 😊\n"
        "YouTube saves a lot of data about you, however I can help you to "
        "get some insight into this data. So for me to help you, you need to "
        "download your data and send me the files `watch-history.json` and "
        "`search-history.json`. Here is a "
        "[Guide](https://github.com/flofriday/youtube-data)"
        " on how to download your personal data.\n\n"
        "Some of the graphs I can create are time-sensetive, so it is "
        "important that I know in which timezone you live in. At the moment I "
        f"think/asume you live in `{user.timezone}`, if this is wrong you "
        "can correct me with the /timezone command.\n\n"
        "This bot is free software, and is developed in the hope to "
        "be useful. Its code is publicly available on "
        "[GitHub](https://github.com/flofriday/youtube-data).\n\n"
        "*Disclaimer:* This is not an official YouTube application, nor am I "
        "[flofriday](https://github.com/flofriday), in any way "
        "associated with YouTube or Google."
    )

    update.message.reply_text(
        message, parse_mode="Markdown", disable_web_page_preview=True
    )


@run_async
def help_command(update, context):
    """Send a message when the command /help is issued."""
    message = (
        "*Things I can do* 🤓\n"
        "/timezone - Set your timezone\n"
        "/info - Informations the bot has about you\n"
        "/statistic - Informations on the bots usage\n"
        "/help - This help message"
    )
    update.message.reply_text(message, parse_mode="Markdown")


@run_async
def info_command(update, context):
    """Show the user what the bot thinks about them"""
    user = User.load(update.effective_user.id)
    message = (
        f"State: {UserState(user.state).name}\nTimezone: {user.timezone}\n"
        f"Number of anaylyzes: {user.analyzes}"
    )
    update.message.reply_text(message, disable_web_page_preview=True)


@run_async
def statistic_command(update, context):
    """Tell the user how many users their are"""
    users, analyzes = User.statistics()

    message = (
        f"*Statistics*\nUsers: *{users}*\nAnalyzes calculated: *{analyzes}*"
    )
    update.message.reply_text(message, parse_mode="Markdown")


@run_async
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


@run_async
def document_message(update, context):
    """React to files the user sends the bot"""

    filename = update.message.document.file_name
    if filename == "search-history.json":
        context.bot.send_chat_action(
            chat_id=update.effective_user.id,
            action=telegram.ChatAction.TYPING,
        )
        analyze_search(update, context)
        return
    elif filename == "watch-history.json":
        context.bot.send_chat_action(
            chat_id=update.effective_user.id,
            action=telegram.ChatAction.TYPING,
        )
        analyze_watch(update, context)
        return

    message = (
        "Sorry, the file must either be named `search-history.json` or "
        "`watch-history.json`. 😔"
    )
    update.message.reply_text(
        message, parse_mode="Markdown", disable_web_page_preview=True
    )


@run_async
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


@run_async
def unknown_message(update, context):
    update.message.reply_text("Sorry, I don't know what you want. 😔")


def analyze_search(update, context):
    document = update.message.document
    f = None
    try:
        f = document.get_file(30)
    except telegram.TelegramError:
        update.message.reply_text(
            "An error occoured while downloading your file."
        )
        return

    # Load the user and the data into a dataframe
    user = User.load(update.effective_user.id)
    json = f.download_as_bytearray().decode("utf-8")
    df = None
    try:
        df = ytd.load_search_history(json, user.timezone)
    except:
        update.message.reply_text(
            "An error occoured while parsing your file. 😵\n"
            "Maybe you uploaded a corrrupted file ?"
        )
        return

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
    send_plot(user, context, plt1)

    # Plot the search activity over time
    plt2 = ytd.search_timeline_plot(df)
    send_plot(user, context, plt2)

    # Update the counter for the user
    user.analyzes += 1
    user.update()
    update.message.reply_text("Done 😊", parse_mode="Markdown")


def analyze_watch(update, context):
    document = update.message.document
    f = None
    try:
        f = document.get_file(30)
    except telegram.TelegramError:
        update.message.reply_text(
            "An error occoured while downloading your file."
        )
        return

    # Load the user and the data into a dataframe
    user = User.load(update.effective_user.id)
    json = f.download_as_bytearray().decode("utf-8")
    df = None
    try:
        df = ytd.load_watch_history(json, user.timezone)
    except:
        update.message.reply_text(
            "An error occoured while parsing your file. 😵\n"
            "Maybe you uploaded a corrrupted file ?"
        )
        return

    # Overall information about the searches
    info_message = (
        f"Videos watched since {df['time'].min().strftime('%b %d %Y')}: "
        f"*{len(df)}*\n"
        f"Average videos per day: "
        f"*{len(df)/((df['time'].max()-df['time'].min()).days):.2f}*"
    )
    update.message.reply_text(info_message, parse_mode="Markdown")

    # Plot the most watched creators
    plt = ytd.creator_plot(df, 24)
    send_plot(user, context, plt)

    # Plot the watch timeline
    plt = ytd.watch_timeline_plot(df)
    send_plot(user, context, plt)

    # Plot the hours the users watches
    plt = ytd.watch_hour_plot(df)
    send_plot(user, context, plt)

    # Update the counter for the user
    user.analyzes += 1
    user.update()
    update.message.reply_text("Done 😊", parse_mode="Markdown")


def main():
    """Start the bot."""

    # Initialize the database
    user.__init__("data/bot.db")

    # Read the config from the environment
    token = os.environ["TELEGRAM_TOKEN"]

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token, use_context=True)
    print("Bot running...")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("timezone", timezone_command))
    dp.add_handler(CommandHandler("info", info_command))
    dp.add_handler(CommandHandler("statistic", statistic_command))
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
