import logging
import os
import json
import pprint

from functools import partial

import redis
import more_itertools

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)

from motlin_api import (
    get_shop_products,
    get_access_token,
    get_product_by_id,
    get_product_image_link,
    download_product_image
)


logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext, motlin_access_token: str):
    goods = get_shop_products(motlin_access_token)["data"]
    prepared_keyboard = [
        InlineKeyboardButton(item["name"], callback_data=item["id"])
        for item in goods
    ]
    keyboard = list(more_itertools.chunked(prepared_keyboard, 2))
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Пожалуйста, выберите товар:',
        reply_markup=reply_markup
    )
    return "HANDLE_MENU"


def buttons(update: Update, context: CallbackContext, motlin_access_token):
    query = update.callback_query
    product = get_product_by_id(
        product_id=query.data,
        api_access_token=motlin_access_token
    )

    image_link = get_product_image_link(product.image_id, motlin_access_token)
    image_extension = download_product_image(
        image_link=image_link,
        product_id=product.id
    )
    product_image_filename = f"{product.id}{image_extension}"
    text = f"{product.name}\n\n" \
           f"Цена: {product.price}\n" \
           f"В наличии: {product.stock} шт.\n\n" \
           f"{product.description}\n"
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open(f"goods_images/{product_image_filename}", "rb") as image:
        context.bot.send_photo(
            caption=text,
            chat_id=query.message.chat_id,
            photo=image,
            reply_markup=reply_markup
        )

    context.bot.deleteMessage(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )
    return "HANDLE_DESCRIPTION"


def return_to_menu(update: Update, context: CallbackContext, motlin_access_token):
    user_reply = update.callback_query.data
    if user_reply == "back_to_menu":
        goods = get_shop_products(motlin_access_token)["data"]
        prepared_keyboard = [
            InlineKeyboardButton(item["name"], callback_data=item["id"])
            for item in goods
        ]
        keyboard = list(more_itertools.chunked(prepared_keyboard, 2))
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.deleteMessage(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )

        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Пожалуйста, выберите товар:',
            reply_markup=reply_markup
        )
        return "HANDLE_MENU"


def echo(update: Update, context: CallbackContext):
    update.message.reply_text(update.message.text)
    return "ECHO"


def handle_messages(update: Update, context: CallbackContext,
                    database: redis, motlin_access_token: str):
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
        "START": partial(start, motlin_access_token=motlin_access_token),
        "ECHO": echo,
        "HANDLE_MENU": partial(buttons, motlin_access_token=motlin_access_token),
        "HANDLE_DESCRIPTION": partial(return_to_menu, motlin_access_token=motlin_access_token)
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
    motlin_client_id = os.environ["MOTLIN_CLIENT_ID"]
    motlin_access_token = get_access_token(
        motlin_client_id=motlin_client_id
    )

    database = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password
    )
    if not database.get("users"):
        users = {}
        setup_redis = json.dumps(users)
        database.set("users", setup_redis)

    updater = Updater(telegram_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(
                handle_messages,
                database=database,
                motlin_access_token=motlin_access_token
            )
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(
                handle_messages,
                database=database,
                motlin_access_token=motlin_access_token
            )
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            'start',
            partial(
                handle_messages,
                database=database,
                motlin_access_token=motlin_access_token
            )
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
