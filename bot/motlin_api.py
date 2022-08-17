import os
import pprint

import requests

from dotenv import load_dotenv


def get_access_token(motlin_client_id: str) -> str:
    url = "https://api.moltin.com/oauth/access_token"
    data = {
        'client_id': motlin_client_id,
        'grant_type': 'implicit',
    }

    response = requests.post(url=url, data=data)
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


def main():
    load_dotenv()
    motlin_client_id = os.environ["MOTLIN_CLIENT_ID"]
    motlin_access_token = get_access_token(motlin_client_id)
    get_shop_products(motlin_access_token)


if __name__ == "__main__":
    main()
