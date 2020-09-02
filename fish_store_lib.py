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


def put_into_cart(access_token, cart_id, prod_id, quantity=1):
    headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
    data = {'data': {'id': prod_id, 'type': 'cart_item', 'quantity': quantity}}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def delete_product_from_cart(access_token, cart_id, prod_id):
    headers = {'Authorization': access_token}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{prod_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def get_cart_items(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    return make_get_request_site(url, headers={'Authorization': access_token})


def get_cart_info(access_token, cart_id):
    cart_info = ['%s\n%s\n%s per kg\n%skg in chart for %s' % (
        ordered_product['name'],
        ordered_product['description'],
        ordered_product['meta']['display_price']['with_tax']['unit']['formatted'],
        ordered_product['quantity'],
        ordered_product['meta']['display_price']['with_tax']['value']['formatted']
    ) for ordered_product in
        get_cart_items(access_token, cart_id)]
    cart_info.append(get_chart_amount(access_token, cart_id))
    return '\n\n'.join(cart_info)


def get_chart_amount(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    cart_price = make_get_request_site(url, headers={'Authorization': access_token})
    return 'Total: %s' % cart_price['meta']['display_price']['with_tax']['formatted']


def get_tg_keyboard(access_token, chat_id, state):
    if state == 'HANDLE_MENU':
        all_products = get_all_products(access_token)
        keyboard = [[InlineKeyboardButton(products['name'], callback_data=products['id'])] for products in all_products]
        keyboard.append([InlineKeyboardButton('Корзина', callback_data=chat_id)])
    elif state == 'HANDLE_DESCRIPTION':
        keyboard = [[
            InlineKeyboardButton('1kg', callback_data=1),
            InlineKeyboardButton('5kg', callback_data=5),
            InlineKeyboardButton('10kg', callback_data=10)],
            [InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')]
        ]
        keyboard.append([InlineKeyboardButton('Корзина', callback_data=chat_id)])
    elif state == 'HANDLE_CART':
        cart_items = get_cart_items(access_token, chat_id)
        keyboard = [[InlineKeyboardButton('Убрать из корзины %s' % cart_item['name'], callback_data=cart_item['id'])] for cart_item in cart_items]
        keyboard.append([InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')])

    return InlineKeyboardMarkup(keyboard)
