import logging
import os
import json

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
    download_product_image,
    add_item_to_cart,
    get_user_cart,
    get_items_from_cart,
    delete_item_from_cart,
    create_customer
)


logger = logging.getLogger(__name__)


def prepare_and_send_back_to_menu_message(update, context, motlin_access_token):
    goods = get_shop_products(motlin_access_token)["data"]
    prepared_keyboard = [
        InlineKeyboardButton(item["name"], callback_data=item["id"])
        for item in goods
    ]
    prepared_keyboard.append(InlineKeyboardButton("Корзина", callback_data="cart"))
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


def prepare_and_send_cart(update, context, motlin_access_token):
    items_in_order = get_items_from_cart(
        user_id=update.callback_query.from_user.id,
        api_access_token=motlin_access_token
    )["data"]

    prepared_items = []
    for item in items_in_order:
        prepared_item = {
            "product_id": item["product_id"],
            "name": item["name"],
            "description": item["description"],
            "quantity": item["quantity"],
            "price": item["meta"]["display_price"]["with_tax"]["value"][
                "formatted"],
            "price_per_unit":
                item["meta"]["display_price"]["with_tax"]["unit"]["formatted"]
        }
        prepared_items.append(prepared_item)

    message_text = ""
    for item in prepared_items:
        order_description = f"{item['name']}\n" \
                            f"{item['description']}\n" \
                            f"{item['price_per_unit']} за 1 штуку.\n" \
                            f"В корзине {item['quantity']} шт. на сумму {item['price']}\n\n"
        message_text += order_description

    prepared_keyboard = []
    for item in prepared_items:
        button = InlineKeyboardButton(
            f"Убрать из корзины {item['name']}",
            callback_data=f"{item['product_id']}_delete")
        prepared_keyboard.append(button)

    prepared_keyboard.append(
        InlineKeyboardButton("Оформить заказ", callback_data="order")
    )
    prepared_keyboard.append(
        InlineKeyboardButton("В меню", callback_data="back_to_menu")
    )

    keyboard = list(more_itertools.chunked(prepared_keyboard, 1))
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_cart = get_user_cart(
        user_id=update.callback_query.from_user.id,
        api_access_token=motlin_access_token
    )
    total_amount = user_cart["data"]["meta"]["display_price"]["with_tax"][
        "formatted"]
    message_text += f"Итого: {total_amount}"

    context.bot.deleteMessage(
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id
    )

    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=message_text,
        reply_markup=reply_markup
    )


def start(update: Update, context: CallbackContext, motlin_access_token: str):
    goods = get_shop_products(motlin_access_token)["data"]
    prepared_keyboard = [
        InlineKeyboardButton(item["name"], callback_data=item["id"])
        for item in goods
    ]
    prepared_keyboard.append(InlineKeyboardButton("Корзина", callback_data="cart"))
    keyboard = list(more_itertools.chunked(prepared_keyboard, 2))
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Пожалуйста, выберите товар:',
        reply_markup=reply_markup
    )
    return "HANDLE_MENU"


def buttons(update: Update, context: CallbackContext, motlin_access_token):
    query = update.callback_query
    if query.data == "cart":
        prepare_and_send_cart(update, context, motlin_access_token)
        return "HANDLE_CART"

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
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data=f"{product.id}_1"),
            InlineKeyboardButton("3", callback_data=f"{product.id}_3"),
            InlineKeyboardButton("5", callback_data=f"{product.id}_5")
        ],
        [
            InlineKeyboardButton("Назад", callback_data="back_to_menu"),
            InlineKeyboardButton("Корзина", callback_data="cart")
        ]
    ]
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
        prepare_and_send_back_to_menu_message(update, context, motlin_access_token)
        return "HANDLE_MENU"

    if user_reply == "cart":
        prepare_and_send_cart(update, context, motlin_access_token)
        return "HANDLE_CART"

    product_id, quantity = user_reply.split("_")
    product = get_product_by_id(
        product_id=product_id,
        api_access_token=motlin_access_token
    )
    update.callback_query.answer(
        text=f"Товар {product.name} в количестве {quantity}шт. "
             f"добавлен в корзину",
        show_alert=True
    )

    add_item_to_cart(
        user_id=update.callback_query.from_user.id,
        api_access_token=motlin_access_token,
        item=product,
        quantity=quantity
    )
    return "HANDLE_DESCRIPTION"


def go_to_cart(update: Update, context: CallbackContext, motlin_access_token):
    query = update.callback_query
    if query.data == "back_to_menu":
        prepare_and_send_back_to_menu_message(update, context,
                                              motlin_access_token)
        return "HANDLE_MENU"

    if "delete" in query.data:
        deleted_product_id, _ = query.data.split("_")
        deleted_product = get_product_by_id(deleted_product_id, motlin_access_token)

        update.callback_query.answer(
            text=f"Товар {deleted_product.name} удален из корзины.",
            show_alert=True
        )

        delete_item_from_cart(
            cart_id=update.callback_query.from_user.id,
            api_access_token=motlin_access_token,
            item=deleted_product
        )

        prepare_and_send_cart(
            update=update,
            context=context,
            motlin_access_token=motlin_access_token
        )
        return "HANDLE_CART"

    if query.data == "order":
        context.bot.deleteMessage(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )

        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Укажите, пожалуйста, ваш емейл:"
        )
        return "WAITING_EMAIL"


def get_customer_email(update: Update, context: CallbackContext,
                       motlin_access_token: str):
    user_email = update.message.text
    create_customer(
        api_access_token=motlin_access_token,
        user_email=user_email,
        user_id=update.message.from_user.id
    )
    return "WAITING_EMAIL"


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
        "HANDLE_MENU": partial(
            buttons, motlin_access_token=motlin_access_token
        ),
        "HANDLE_DESCRIPTION": partial(
            return_to_menu, motlin_access_token=motlin_access_token
        ),
        "HANDLE_CART": partial(
            go_to_cart, motlin_access_token=motlin_access_token
        ),
        "WAITING_EMAIL": partial(
            get_customer_email, motlin_access_token=motlin_access_token
        )
    }
    state_handler = states_functions[user_state]

    next_state = state_handler(update, context)
    users[chat_id] = next_state
    database.set("users", json.dumps(users))


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
    motlin_client_secret = os.environ["MOTLIN_CLIENT_SECRET"]

    motlin_access_token = get_access_token(
        motlin_client_id=motlin_client_id,
        motlin_client_secret=motlin_client_secret
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
