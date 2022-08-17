import logging
import os
import json

from functools import partial

import redis

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    update.message.reply_text(text='Привет!')
    return "ECHO"


def echo(update: Update, context: CallbackContext):
    update.message.reply_text(update.message.text)
    return "ECHO"


def handle_messages(update: Update, context: CallbackContext, database):
    if update.message:
        user_reply = update.message.text
        chat_id = str(update.message.chat_id)
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = str(update.callback_query.message.chat_id)
    else:
        return

    users = json.loads(database.get("users").decode("utf-8"))

    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = users[chat_id]

    states_functions = {
        'START': start,
        "ECHO": echo
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        users[chat_id] = next_state
        database.set("users", json.dumps(users))
    except Exception as err:
        print(err)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()
    telegram_bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    redis_host = os.environ["REDIS_HOST"]
    redis_port = os.environ["REDIS_PORT"]
    redis_password = os.environ["REDIS_PASSWORD"]
    updater = Updater(telegram_bot_token)

    database = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password
    )
    if not database.get("users"):
        users = {}
        setup_redis = json.dumps(users)
        database.set("users", setup_redis)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(handle_messages, database=database)
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(handle_messages, database=database)
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            'start',
            partial(handle_messages, database=database)
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
