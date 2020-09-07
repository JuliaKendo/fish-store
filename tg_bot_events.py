import motlin_lib
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

LIMIT_PRODS_PER_PAGE = 5


def get_store_menu(access_token, chat_id, page=None):
    page = int(page) if page else 0
    all_products, max_pages = motlin_lib.get_products(access_token, page, LIMIT_PRODS_PER_PAGE)
    products_in_cart = {
        cart_item['product_id']: cart_item['quantity']
        for cart_item in motlin_lib.get_cart_items(access_token, chat_id)
    }
    keyboard = [
        [InlineKeyboardButton(
            '%s %s' % (
                products['name'], '({}kg)'.format(products_in_cart[products['id']]) if products_in_cart.get(products['id']) else ''
            ), callback_data=products['id']
        )] for products in all_products
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data=chat_id)])
    if max_pages == 1:
        return InlineKeyboardMarkup(keyboard)
    if page > 0 and page < max_pages:
        keyboard.append([
            InlineKeyboardButton('<', callback_data='%d' % (page - LIMIT_PRODS_PER_PAGE)),
            InlineKeyboardButton('>', callback_data='%d' % (page + LIMIT_PRODS_PER_PAGE))
        ])
    elif page == 0:
        keyboard.append([
            InlineKeyboardButton('>', callback_data='%d' % (page + LIMIT_PRODS_PER_PAGE))
        ])
    elif page >= max_pages:
        keyboard.append([
            InlineKeyboardButton('<', callback_data='%d' % (page - LIMIT_PRODS_PER_PAGE))
        ])
    return InlineKeyboardMarkup(keyboard)


def get_product_card_menu(access_token, chat_id):
    keyboard = [[
        InlineKeyboardButton('1kg', callback_data=1),
        InlineKeyboardButton('5kg', callback_data=5),
        InlineKeyboardButton('10kg', callback_data=10)],
        [InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')]
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data=chat_id)])
    return InlineKeyboardMarkup(keyboard)


def get_cart_menu(access_token, chat_id):
    cart_items = motlin_lib.get_cart_items(access_token, chat_id)
    keyboard = [
        [
            InlineKeyboardButton(
                'Убрать из корзины %s' % cart_item['name'],
                callback_data=cart_item['id']
            )
        ] for cart_item in cart_items
    ]
    keyboard.append([InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')])
    keyboard.append([InlineKeyboardButton('Оплата', callback_data=chat_id)])
    return InlineKeyboardMarkup(keyboard)


def get_confirm_menu(access_token, chat_id):
    keyboard = [
        [InlineKeyboardButton('Верно', callback_data='HANDLE_MENU')],
        [InlineKeyboardButton('Не верно', callback_data='WAITING_EMAIL')]
    ]
    return InlineKeyboardMarkup(keyboard)


def show_store_menu(bot, chat_id, motlin_token, delete_message_id=0, page=None):
    reply_markup = get_store_menu(motlin_token, chat_id, page)
    bot.send_message(chat_id=chat_id, text="Please choise:", reply_markup=reply_markup)
    if delete_message_id:
        bot.delete_message(chat_id=chat_id, message_id=delete_message_id)


def show_product_card(bot, chat_id, motlin_token, product_id, delete_message_id=0):
    product_caption, product_image = motlin_lib.get_product_info(motlin_token, product_id)
    reply_markup = get_product_card_menu(motlin_token, chat_id)
    bot.send_photo(
        chat_id=chat_id,
        photo=product_image,
        caption=product_caption,
        reply_markup=reply_markup,
        parse_mode='html'
    )
    if delete_message_id:
        bot.delete_message(chat_id=chat_id, message_id=delete_message_id)


def add_product_to_cart(chat_id, motlin_token, product_id, query):
    product_quantity = query.data
    if product_quantity:
        motlin_lib.put_into_cart(motlin_token, chat_id, product_id, int(product_quantity))
        query.answer("Товар добавлен в корзину")


def show_products_in_cart(bot, chat_id, motlin_token, delete_message_id=0):
    cart_info = motlin_lib.get_cart_info(motlin_token, str(chat_id))
    reply_markup = get_cart_menu(motlin_token, chat_id)
    bot.send_message(
        chat_id=chat_id,
        text=cart_info,
        reply_markup=reply_markup,
        parse_mode='html'
    )
    if delete_message_id:
        bot.delete_message(chat_id=chat_id, message_id=delete_message_id)


def confirm_email(bot, chat_id, motlin_token, customer_email):
    reply_markup = get_confirm_menu(motlin_token, chat_id)
    bot.send_message(
        chat_id=chat_id,
        text='Ваш еmail: %s' % customer_email,
        reply_markup=reply_markup)


def finish_order(bot, chat_id, delete_message_id=0):
    bot.send_message(chat_id=chat_id, text='Благодарим за заказ. Менеждер свяжется с Вами в бижайшее время.')
    bot.delete_message(chat_id=chat_id, message_id=delete_message_id)
