import os

from typing import NamedTuple

import requests

from dotenv import load_dotenv


class Product(NamedTuple):
    name: str
    price: str
    stock: int
    description: str


def get_access_token(motlin_client_id: str) -> str:
    url = "https://api.moltin.com/oauth/access_token"
    request_data = {
        'client_id': motlin_client_id,
        'grant_type': 'implicit',
    }

    response = requests.post(url=url, data=request_data)
    response.raise_for_status()

    api_response = response.json()
    motlin_access_token = api_response["access_token"]
    os.environ["MOTLIN_ACCESS_TOKEN"] = motlin_access_token
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


def add_item_to_cart(user_id: str, api_access_token: str, item: dict) -> None:
    url = f"https://api.moltin.com/v2/carts/{user_id}/items"
    headers = {
        "Authorization": f"Bearer {api_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "type": "custom_item",
            "name": item["name"],
            "sku": item["sku"],
            "description": item["description"],
            "quantity": 1,
            "price": item["price"][0]
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
    prodcut_stock = api_response["data"]["meta"]["stock"]["level"]
    product_description = api_response["data"]["description"]
    return Product(name=product_name, price=product_price,
                   stock=prodcut_stock, description=product_description)


def main():
    load_dotenv()
    motlin_client_id = os.environ["MOTLIN_CLIENT_ID"]
    motlin_access_token = get_access_token(motlin_client_id)
    all_products = get_shop_products(motlin_access_token)
    user_choice = all_products["data"][1]
    user_id = "abc"
    add_item_to_cart(
        user_id=user_id,
        api_access_token=motlin_access_token,
        item=user_choice
    )
    get_items_from_cart(user_id=user_id, api_access_token=motlin_access_token)


if __name__ == "__main__":
    main()
