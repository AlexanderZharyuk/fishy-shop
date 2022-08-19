import os
import time

from typing import NamedTuple

import requests

from requests.exceptions import HTTPError


class Product(NamedTuple):
    name: str
    price: str
    stock: int
    description: str
    image_id: str
    id: str


def get_access_token(moltin_client_id: str, moltin_client_secret: str) -> str:
    url = "https://api.moltin.com/oauth/access_token"
    request_data = {
        "client_id": moltin_client_id,
        "grant_type": "client_credentials",
        "client_secret": moltin_client_secret
    }

    response = requests.post(url=url, data=request_data)
    response.raise_for_status()

    moltin = response.json()
    moltin_access_token = moltin["access_token"]
    return moltin_access_token


def get_access_token_status(access_token: str):
    url = "https://api.moltin.com/v2/products"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers)
        response.raise_for_status()
    except HTTPError:
        return False
    return True


def get_shop_products(api_access_token: str) -> dict:
    url = "https://api.moltin.com/v2/products"
    headers = {
        "Authorization": f"Bearer {api_access_token}"
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    moltin = response.json()

    return moltin


def get_user_cart(user_id: str, api_access_token: str) -> dict:
    url = f"https://api.moltin.com/v2/carts/{user_id}"
    headers = {
        "Authorization": f"Bearer {api_access_token}"
    }

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()

    moltin = response.json()
    return moltin


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

    moltin = response.json()
    return moltin


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

    moltin = response.json()
    product_name = moltin["data"]["name"]
    product_price = moltin["data"]["meta"]["display_price"]["without_tax"]["formatted"]
    product_stock = moltin["data"]["meta"]["stock"]["level"]
    product_description = moltin["data"]["description"]
    product_image_id = moltin["data"]["relationships"]["main_image"]["data"]["id"]
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

    moltin = response.json()
    product_image = moltin["data"]["link"]["href"]
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
