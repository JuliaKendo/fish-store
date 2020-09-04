import db_lib
from fish_store_lib import get_tg_keyboard
from fish_store_lib import get_product_info
from fish_store_lib import put_into_cart, get_cart_info


def show_store_menu(bot, chat_id, motlin_token, delete_message_id=0):
    state = 'HANDLE_MENU'
    reply_markup = get_tg_keyboard(motlin_token, chat_id, state)
    bot.send_message(chat_id=chat_id, text="Please choise:", reply_markup=reply_markup)
    if delete_message_id:
        bot.delete_message(chat_id=chat_id, message_id=delete_message_id)
    return state


def show_product_card(bot, chat_id, motlin_token, product_id, delete_message_id=0):
    state = 'HANDLE_DESCRIPTION'
    db_lib.RedisDb().set_value(f'{chat_id}_chosen_product', product_id)
    product_caption, product_image = get_product_info(motlin_token, product_id)
    reply_markup = get_tg_keyboard(motlin_token, chat_id, state)
    bot.send_photo(chat_id=chat_id, photo=product_image, caption=product_caption, reply_markup=reply_markup)
    if delete_message_id:
        bot.delete_message(chat_id=chat_id, message_id=delete_message_id)
    return state


def add_product_to_cart(chat_id, motlin_token, query):
    chosen_product = db_lib.RedisDb().get_value(f'{chat_id}_chosen_product')
    product_quantity = query.data
    if product_quantity:
        put_into_cart(motlin_token, chat_id, chosen_product, int(product_quantity))
        query.answer("Товар добавлен в корзину")
    return 'HANDLE_DESCRIPTION'


def show_products_in_cart(bot, chat_id, motlin_token, delete_message_id=0):
    state = 'HANDLE_CART'
    chart_info = get_cart_info(motlin_token, str(chat_id))
    reply_markup = get_tg_keyboard(motlin_token, chat_id, state)
    bot.send_message(chat_id=chat_id, text=chart_info, reply_markup=reply_markup)
    if delete_message_id:
        bot.delete_message(chat_id=chat_id, message_id=delete_message_id)
    return state


def confirm_email(bot, chat_id, motlin_token, customer_email):
    state = 'WAITING_EMAIL'
    reply_markup = get_tg_keyboard(motlin_token, chat_id, state)
    bot.send_message(chat_id=chat_id, text='Ваш еmail: %s' % customer_email, reply_markup=reply_markup)
    return state


def finish_order(bot, chat_id, delete_message_id=0):
    bot.send_message(chat_id=chat_id, text='Благодарим за заказ. Менеждер свяжется с Вами в бижайшее время.')
    bot.delete_message(chat_id=chat_id, message_id=delete_message_id)
    return 'HANDLE_MENU'
