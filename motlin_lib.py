import requests


def get_moltin_access_token(client_secret, client_id):
    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
    )
    response.raise_for_status()
    moltin_token = response.json()
    return moltin_token['access_token'], moltin_token['expires']


def execute_get_request(url, headers={}, data={}):
    response = requests.get(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['data']


def get_products(access_token, page=0, limit_products_per_page=0):
    response = requests.get(
        'https://api.moltin.com/v2/products?page[limit]=%s&page[offset]=%s' % (limit_products_per_page, page),
        headers={'Authorization': access_token}
    )

    response.raise_for_status()
    products = response.json()
    return products['data'], products['meta']['page']['total']


def get_quantity_product_in_stock(access_token, product_id):
    product_data = execute_get_request(
        f'https://api.moltin.com/v2/inventories/{product_id}',
        headers={'Authorization': access_token}
    )
    return product_data['total']


def get_product_image(access_token, product_data):
    image_id = product_data['relationships']['main_image']['data']['id']
    product_data = execute_get_request(
        f'https://api.moltin.com/v2/files/{image_id}',
        headers={'Authorization': access_token}
    )
    return product_data['link']['href']


def get_product_info(access_token, product_id):
    product_data = execute_get_request(
        f'https://api.moltin.com/v2/products/{product_id}',
        headers={'Authorization': access_token}
    )
    product_price = product_data['price'][0]
    return '<b>%s</b>\n\n%s %s за kg\n%skg на складе\n\n<i>%s</i>' % (
        product_data['name'],
        product_price['currency'],
        product_price['amount'],
        get_quantity_product_in_stock(access_token, product_id),
        product_data['description']
    ), get_product_image(access_token, product_data)


def put_into_cart(access_token, cart_id, prod_id, quantity=1):
    response = requests.post(
        f'https://api.moltin.com/v2/carts/{cart_id}/items',
        headers={'Authorization': access_token, 'Content-Type': 'application/json'},
        json={'data': {'id': prod_id, 'type': 'cart_item', 'quantity': quantity}}
    )
    response.raise_for_status()


def delete_from_cart(access_token, cart_id, prod_id):
    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{prod_id}',
        headers={'Authorization': access_token}
    )
    response.raise_for_status()


def get_cart_items(access_token, cart_id):
    return execute_get_request(
        f'https://api.moltin.com/v2/carts/{cart_id}/items',
        headers={'Authorization': access_token}
    )


def get_cart_info(access_token, cart_id):
    cart_info = ['<b>%s</b>\n<i>%s</i>\n%s за kg\n%skg в корзине: %s' % (
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
    cart_price = execute_get_request(
        f'https://api.moltin.com/v2/carts/{cart_id}',
        headers={'Authorization': access_token}
    )
    return 'Итого: %s' % cart_price['meta']['display_price']['with_tax']['formatted']


def add_new_customer(access_token, email):
    headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
    data = {'data': {'type': 'customer', 'name': email.split('@')[0], 'email': email}}
    response = requests.post(
        'https://api.moltin.com/v2/customers',
        headers=headers,
        json=data
    )
    response.raise_for_status()


def get_customer_id(access_token, email):
    found_users = execute_get_request(
        'https://api.moltin.com/v2/customers',
        {'Authorization': access_token}
    )
    found_user = [user['id'] for user in found_users if user['email'] == email]
    return found_user[0] if found_user else None
