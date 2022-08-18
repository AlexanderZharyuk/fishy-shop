import os
import time

from typing import NamedTuple

import requests
import redis

from dotenv import load_dotenv


class Product(NamedTuple):
    name: str
    price: str
    stock: int
    description: str
    image_id: str
    id: str


def get_access_token(motlin_client_id: str, motlin_client_secret: str) -> str:
    url = "https://api.moltin.com/oauth/access_token"
    request_data = {
        "client_id": motlin_client_id,
        "grant_type": "client_credentials",
        "client_secret": motlin_client_secret
    }

    response = requests.post(url=url, data=request_data)
    response.raise_for_status()

    api_response = response.json()
    motlin_access_token = api_response["access_token"]
    return motlin_access_token


def get_shop_products(api_access_token: str) -> dict:
    url = "https://api.moltin.com/v2/products"
    headers = {
        "Authorization": f"Bearer {api_access_token}"
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    api_response = response.json()

    return api_response


def get_user_cart(user_id: str, api_access_token: str) -> dict:
    url = f"https://api.moltin.com/v2/carts/{user_id}"
    headers = {
        "Authorization": f"Bearer {api_access_token}"
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()

    api_response = response.json()
    return api_response


def add_item_to_cart(user_id: str, api_access_token: str,
                     item: Product, quantity: str) -> None:
    url = f"https://api.moltin.com/v2/carts/{user_id}/items"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "type": "cart_item",
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "quantity": int(quantity),
        }
    }

    response = requests.post(url=url, headers=headers, json=payload)
    response.raise_for_status()


def get_items_from_cart(user_id: str, api_access_token: str) -> dict:
    url = f"https://api.moltin.com/v2/carts/{user_id}/items"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()

    api_response = response.json()
    return api_response


def delete_item_from_cart(cart_id: str, api_access_token: str, item: Product):
    product_id_in_cart = [product["id"] for product in get_items_from_cart(
            cart_id, api_access_token)["data"] if
        product["product_id"] == item.id][0]

    url = f"https://api.moltin.com/v2/carts/{cart_id}/items/{product_id_in_cart}"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }

    response = requests.delete(url=url, headers=headers)
    response.raise_for_status()


def get_product_by_id(product_id: str, api_access_token: str) -> Product:
    url = f"https://api.moltin.com/v2/products/{product_id}"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()

    api_response = response.json()
    product_name = api_response["data"]["name"]
    product_price = api_response["data"]["meta"]["display_price"]["without_tax"]["formatted"]
    product_stock = api_response["data"]["meta"]["stock"]["level"]
    product_description = api_response["data"]["description"]
    product_image_id = api_response["data"]["relationships"]["main_image"]["data"]["id"]
    return Product(name=product_name, price=product_price,
                   stock=product_stock, description=product_description,
                   image_id=product_image_id, id=product_id)


def get_product_image_link(image_id: str, api_access_token: str) -> str:
    url = f"https://api.moltin.com/v2/files/{image_id}"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()

    api_response = response.json()
    product_image = api_response["data"]["link"]["href"]
    return product_image


def download_product_image(image_link: str, product_id: str) -> str:
    response = requests.get(image_link)
    response.raise_for_status()

    _, file_extension = os.path.splitext(image_link)
    os.makedirs("goods_images", exist_ok=True)

    filename = f"goods_images/{product_id}{file_extension}"
    with open(filename, "wb") as image_file:
        image_file.write(response.content)

    return file_extension


def create_customer(api_access_token: str, user_id: str, user_email: str):
    url = "https://api.moltin.com/v2/customers"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
    }
    payload = {
        "data": {
            "type": "customer",
            "name": str(user_id),
            "email": user_email
        }
    }
    response = requests.post(url=url, headers=headers, json=payload)
    response.raise_for_status()


def main():
    motlin_client_id = os.environ["MOTLIN_CLIENT_ID"]
    motlin_client_secret = os.environ["MOTLIN_CLIENT_SECRET"]

    access_token = get_access_token(
        motlin_client_id=motlin_client_id,
        motlin_client_secret=motlin_client_secret
    )
    database.set("motlin_access_token", access_token)


if __name__ == "__main__":
    load_dotenv()
    redis_host = os.environ["REDIS_HOST"]
    redis_port = os.environ["REDIS_PORT"]
    redis_password = os.environ["REDIS_PASSWORD"]
    database = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password
    )
    while True:
        # API-токен motlin обновляется каждый час (3600 секунд).
        # Исходя из этого обновляем его значение в редисе каждый час.
        main()
        time.sleep(3500)
