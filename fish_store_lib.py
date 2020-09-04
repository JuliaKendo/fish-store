import re
import db_lib
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

LIMIT_PAGE = 2


def get_moltin_access_token(client_secret, client_id):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()
    moltin_token = response.json()
    return moltin_token['access_token'], moltin_token['expires']


def execute_get_request(url, headers={}, data={}):
    response = requests.get(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['data']


def get_all_products(access_token, page=0):
    url = 'https://api.moltin.com/v2/products?page[limit]=%d&page[offset]=%d' % (LIMIT_PAGE, page)
    response = requests.get(url, headers={'Authorization': access_token})
    response.raise_for_status()
    all_products = response.json()
    return all_products['data'], all_products['meta']['page']['total']


def get_total_in_stock(access_token, product_id):
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    product_data = execute_get_request(url, headers={'Authorization': access_token})
    return product_data['total']


def get_product_image(access_token, product_data):
    image_id = product_data['relationships']['main_image']['data']['id']
    url = f'https://api.moltin.com/v2/files/{image_id}'
    product_data = execute_get_request(url, headers={'Authorization': access_token})
    return product_data['link']['href']


def get_product_info(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    product_data = execute_get_request(url, headers={'Authorization': access_token})
    product_price = product_data['price'][0]
    return '%s\n\n%s %s за kg\n%skg на складе\n\n%s' % (
        product_data['name'],
        product_price['currency'],
        product_price['amount'],
        get_total_in_stock(access_token, product_id),
        product_data['description']
    ), get_product_image(access_token, product_data)


def put_into_cart(access_token, cart_id, prod_id, quantity=1):
    headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
    data = {'data': {'id': prod_id, 'type': 'cart_item', 'quantity': quantity}}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def delete_from_cart(access_token, cart_id, prod_id):
    headers = {'Authorization': access_token}
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{prod_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def get_cart_items(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    return execute_get_request(url, headers={'Authorization': access_token})


def get_cart_info(access_token, cart_id):
    cart_info = ['%s\n%s\n%s per kg\n%skg in chart for %s' % (
        ordered_product['name'],
        ordered_product['description'],
        ordered_product['meta']['display_price']['with_tax']['unit']['formatted'],
        ordered_product['quantity'],
        ordered_product['meta']['display_price']['with_tax']['value']['formatted']
    ) for ordered_product in
        get_cart_items(access_token, cart_id)]
    cart_info.append(get_cart_amount(access_token, cart_id))
    return '\n\n'.join(cart_info)


def get_cart_amount(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    cart_price = execute_get_request(url, headers={'Authorization': access_token})
    return 'Итого: %s' % cart_price['meta']['display_price']['with_tax']['formatted']


def add_new_customer(access_token, email):
    # https://web.izjum.com/regexp-email-url-phone
    pattern = r'^(([a-z0-9_-]+\.)*[a-z0-9_-]+)(@)([a-z0-9_-]+(\.[a-z0-9_-]+)*\.[a-z]{2,6})$'
    email_parts = re.findall(pattern, email)
    if email_parts and '@' in email_parts[0]:
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        data = {'data': {'type': 'customer', 'name': email_parts[0][0], 'email': email}}
        url = f'https://api.moltin.com/v2/customers'
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()


def get_customer_id(access_token, email):
    headers = {'Authorization': access_token}
    data = {'filter': f'eq(email,{email})'}
    url = f'https://api.moltin.com/v2/customers'
    found_user = execute_get_request(url, headers, data)
    if found_user:
        return found_user[0]['id']


def get_current_page(page_identifier):
    page_number = re.findall(r'[0-9]+$', page_identifier)
    return int(page_number[0]) if page_number else 0


def get_store_menu(access_token, chat_id):
    page = int(db_lib.RedisDb().get_value('current_page'))
    all_products, max_pages = get_all_products(access_token, page)
    keyboard = [[InlineKeyboardButton(products['name'], callback_data=products['id'])] for products in all_products]
    if page > 0 and page < max_pages:
        keyboard.append([
            InlineKeyboardButton('<', callback_data='page%d' % (page - LIMIT_PAGE)),
            InlineKeyboardButton('>', callback_data='page%d' % (page + LIMIT_PAGE))
        ])
    elif page == 0:
        keyboard.append([
            InlineKeyboardButton('>', callback_data='page%d' % (page + LIMIT_PAGE))
        ])
    elif page >= max_pages:
        keyboard.append([
            InlineKeyboardButton('<', callback_data='page%d' % (page - LIMIT_PAGE))
        ])
    keyboard.append([InlineKeyboardButton('Корзина', callback_data=chat_id)])
    return keyboard


def get_product_card_menu(access_token, chat_id):
    keyboard = [[
        InlineKeyboardButton('1kg', callback_data=1),
        InlineKeyboardButton('5kg', callback_data=5),
        InlineKeyboardButton('10kg', callback_data=10)],
        [InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')]
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data=chat_id)])
    return keyboard


def get_cart_menu(access_token, chat_id):
    cart_items = get_cart_items(access_token, chat_id)
    keyboard = [[InlineKeyboardButton('Убрать из корзины %s' % cart_item['name'], callback_data=cart_item['id'])] for cart_item in cart_items]
    keyboard.append([InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')])
    keyboard.append([InlineKeyboardButton('Оплата', callback_data=chat_id)])
    return keyboard


def get_confirm_menu(access_token, chat_id):
    keyboard = [
        [InlineKeyboardButton('Верно', callback_data='HANDLE_MENU')],
        [InlineKeyboardButton('Не верно', callback_data='WAITING_EMAIL')]
    ]
    return keyboard


def get_tg_keyboard(access_token, chat_id, state):
    menu_states_functions = {
        'HANDLE_MENU': get_store_menu,
        'HANDLE_DESCRIPTION': get_product_card_menu,
        'HANDLE_CART': get_cart_menu,
        'WAITING_EMAIL': get_confirm_menu
    }
    menu_state_function = menu_states_functions[state]
    return InlineKeyboardMarkup(menu_state_function(access_token, chat_id))
