import logging
import logger_tools

import motlin_lib
import os
import redis_lib

from datetime import datetime
from dotenv import load_dotenv

from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, MessageHandler, CommandHandler
from tg_bot_events import add_product_to_cart, confirm_email
from tg_bot_events import show_store_menu, show_product_card
from tg_bot_events import show_products_in_cart, finish_order

from validate_email import validate_email


logger = logging.getLogger('fish_store_bot')


class TgDialogBot(object):

    def __init__(self, tg_token, states_functions, redis_conn, motlin_params):
        self.updater = Updater(token=tg_token)
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.handle_users_reply))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.handle_users_reply))
        self.updater.dispatcher.add_handler(CommandHandler('start', self.handle_users_reply))
        self.updater.dispatcher.add_error_handler(self.error)
        self.states_functions = states_functions
        self.redis_conn = redis_conn
        self.motlin_params = motlin_params
        self.motlin_token, self.token_expires = None, 0

    def start(self):
        self.updater.start_polling()

    def update_motlin_token(self):
        if self.token_expires < datetime.now().timestamp():
            self.motlin_token, self.token_expires = motlin_lib.get_moltin_access_token(
                client_secret=self.motlin_params['MOLTIN_CLIENT_SECRET'],
                client_id=self.motlin_params['MOLTIN_CLIENT_ID']
            )

    def handle_users_reply(self, bot, update):
        self.update_motlin_token()
        if update.message:
            user_reply = update.message.text
            chat_id = update.message.chat_id
        elif update.callback_query:
            user_reply = update.callback_query.data
            chat_id = update.callback_query.message.chat_id
        else:
            return

        if user_reply == '/start':
            user_state = 'START'
        else:
            user_state = self.redis_conn.get_value(chat_id, 'state')

        state_handler = self.states_functions[user_state]
        next_state = state_handler(bot, update, motlin_token=self.motlin_token, redis_conn=self.redis_conn)
        self.redis_conn.add_value(chat_id, 'state', next_state)

    def error(self, bot, update, error):
        logger.exception(f'Ошибка бота: {error}')


def start(bot, update, motlin_token, redis_conn):
    current_page = redis_conn.get_value(update.message.chat_id, 'current_page')
    show_store_menu(bot, update.message.chat_id, motlin_token, page=current_page)
    return 'HANDLE_MENU'


def handle_menu(bot, update, motlin_token, redis_conn):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == str(chat_id):
        show_products_in_cart(bot, chat_id, motlin_token, query.message.message_id)
        return 'HANDLE_CART'
    elif query.data.isdecimal():
        redis_conn.add_value(chat_id, 'current_page', query.data)
        show_store_menu(bot, chat_id, motlin_token, query.message.message_id, query.data)
        return 'HANDLE_MENU'
    else:
        redis_conn.add_value(chat_id, 'chosen_product', query.data)
        show_product_card(
            bot,
            chat_id,
            motlin_token,
            query.data,
            query.message.message_id
        )
        return 'HANDLE_DESCRIPTION'


def handle_description(bot, update, motlin_token, redis_conn):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'HANDLE_MENU':
        current_page = redis_conn.get_value(chat_id, 'current_page')
        show_store_menu(bot, chat_id, motlin_token, query.message.message_id, current_page)
        return query.data
    elif query.data == str(chat_id):
        show_products_in_cart(bot, chat_id, motlin_token, query.message.message_id)
        return 'HANDLE_CART'
    else:
        product_id = redis_conn.get_value(chat_id, 'chosen_product')
        add_product_to_cart(chat_id, motlin_token, product_id, query)
        return 'HANDLE_DESCRIPTION'


def handle_cart(bot, update, motlin_token, redis_conn):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'HANDLE_MENU':
        current_page = redis_conn.get_value(chat_id, 'current_page')
        show_store_menu(bot, chat_id, motlin_token, query.message.message_id, current_page)
        return query.data
    elif query.data == str(chat_id):
        bot.send_message(chat_id=chat_id, text='Пришлите, пожалуйста, Ваш email')
        return 'WAITING_EMAIL'
    else:
        motlin_lib.delete_from_cart(motlin_token, chat_id, query.data)
        show_products_in_cart(bot, chat_id, motlin_token, query.message.message_id)
        return 'HANDLE_CART'


def waiting_email(bot, update, motlin_token, redis_conn):
    query = update.callback_query
    if query and query.data == 'HANDLE_MENU':
        finish_order(bot, query.message.chat_id, query.message.message_id)
        return query.data
    elif query and query.data == 'WAITING_EMAIL':
        bot.send_message(chat_id=query.message.chat_id, text='Пришлите, пожалуйста, Ваш email')
        return query.data
    elif update.message.text and validate_email(update.message.text):
        if not motlin_lib.get_customer_id(motlin_token, update.message.text):
            motlin_lib.add_new_customer(motlin_token, update.message.text)
        confirm_email(bot, update.message.chat_id, motlin_token, update.message.text)
        return 'WAITING_EMAIL'
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Вы ввели не корректный email. Поробуйте еще раз:')
        return 'WAITING_EMAIL'


def launch_store_bot(states_functions, motlin_params):
    try:
        redis_conn = redis_lib.RedisDb(
            os.getenv('REDIS_HOST'),
            os.getenv('REDIS_PORT'),
            os.getenv('REDIS_PASSWORD')
        )
        bot = TgDialogBot(
            os.getenv('TG_ACCESS_TOKEN'),
            states_functions,
            redis_conn,
            motlin_params
        )
        bot.start()
    except Exception as error:
        logger.exception(f'Ошибка бота: {error}')
        launch_store_bot(states_functions, motlin_params)


def main():
    load_dotenv()

    logger_tools.initialize_logger(
        logger,
        os.getenv('TG_LOG_TOKEN'),
        os.getenv('TG_CHAT_ID')
    )

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': waiting_email
    }

    motlin_params = {
        'MOLTIN_CLIENT_ID': os.getenv('MOLTIN_CLIENT_ID'),
        'MOLTIN_CLIENT_SECRET': os.getenv('MOLTIN_CLIENT_SECRET')
    }

    launch_store_bot(states_functions, motlin_params)


if __name__ == '__main__':
    main()
