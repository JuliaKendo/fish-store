import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_moltin_access_token(client_secret, client_id):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()['access_token']


def make_get_request_site(url, headers={}, data={}):
    response = requests.get(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['data']


def get_all_products(access_token):
    url = 'https://api.moltin.com/v2/products'
    return make_get_request_site(url, headers={'Authorization': access_token})


def get_product_price(product_data):
    product_price = product_data['price'][0]
    return product_price['amount'], product_price['currency']


def get_total_in_stock(access_token, product_id):
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    product_data = make_get_request_site(url, headers={'Authorization': access_token})
    return product_data['total']


def get_product_image(access_token, product_data):
    image_id = product_data['relationships']['main_image']['data']['id']
    url = f'https://api.moltin.com/v2/files/{image_id}'
    product_data = make_get_request_site(url, headers={'Authorization': access_token})
    return product_data['link']['href']


def get_product_info(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    product_data = make_get_request_site(url, headers={'Authorization': access_token})
    product_price, product_currency = get_product_price(product_data)
    return '%s\n\n%s %s per kg\n%skg in stock\n\n%s' % (
        product_data['name'],
        product_currency,
        product_price,
        get_total_in_stock(access_token, product_id),
        product_data['description']
    ), get_product_image(access_token, product_data)


def put_into_chart(access_token, chart_id, prod_id, quantity=1):
    headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
    data = {'data': {'id': prod_id, 'type': 'cart_item', 'quantity': quantity}}
    url = f'https://api.moltin.com/v2/carts/{chart_id}/items'
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def get_chart_items(access_token, chart_id):
    url = f'https://api.moltin.com/v2/carts/{chart_id}/items'
    return make_get_request_site(url, headers={'Authorization': access_token})


def get_tg_keyboard(access_token, state):
    if state == 'HANDLE_MENU':
        all_products = get_all_products(access_token)
        keyboard = [[InlineKeyboardButton(products['name'], callback_data=products['id'])] for products in all_products]
    elif state == 'HANDLE_DESCRIPTION':
        keyboard = [[
            InlineKeyboardButton('1kg', callback_data=1),
            InlineKeyboardButton('5kg', callback_data=5),
            InlineKeyboardButton('10kg', callback_data=10)],
            [InlineKeyboardButton('Назад', callback_data='HANDLE_MENU')]
        ]

    return InlineKeyboardMarkup(keyboard)

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
