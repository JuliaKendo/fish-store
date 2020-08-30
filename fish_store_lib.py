import pprint
import requests
from telegram import InlineKeyboardButton


def get_moltin_access_token(client_secret, client_id):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()['access_token']


def get_all_products(access_token):
    response = requests.get('https://api.moltin.com/v2/products', headers={'Authorization': access_token})
    response.raise_for_status()
    return response.json()


def put_into_chart(access_token, chart_id, prod_id, quantity=1, price=0):
    headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
    data = {'data': {'id': prod_id, 'type': 'cart_item', 'quantity': quantity}}
    response = requests.post(f'https://api.moltin.com/v2/carts/:{chart_id}/items', headers=headers, json=data)
    response.raise_for_status()


def get_chart_items(access_token, chart_id):
    headers = {'Authorization': access_token}
    response = requests.get(f'https://api.moltin.com/v2/carts/:{chart_id}/items', headers=headers)
    response.raise_for_status()
    return response.json()


def get_tg_keyboard(access_token):
    keyboard = []
    all_products = get_all_products(access_token)['data']
    for products in all_products:
        keyboard.append([InlineKeyboardButton(products['name'], callback_data=products['id'])])
    return keyboard


# try:
#     access_token = get_access_token()
#     chart_id = 'abc'
#     pprint.pprint(access_token)
#     all_products = get_all_products(access_token)['data']
#     first_product = all_products[1]
#     put_into_chart(access_token, chart_id, first_product['id'], 1)
#     chart = get_chart_items(access_token, chart_id)
#     print(chart)
# except requests.HTTPError as error:
#     print(error.response.content.decode())
