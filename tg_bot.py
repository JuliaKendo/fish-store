from telegram.ext import Filters, Updater
from fish_store_lib import delete_product_from_cart
from tg_bot_events import show_store_menu, show_product_card
from tg_bot_events import show_products_in_cart, add_product_to_cart
from telegram.ext import CallbackQueryHandler, MessageHandler, CommandHandler


class TgDialogBot(object):

    def __init__(self, tg_token, motlin_token, redis_db, states_functions):
        self.updater = Updater(token=tg_token)
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.handle_users_reply))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.handle_users_reply))
        self.updater.dispatcher.add_handler(CommandHandler('start', self.handle_users_reply))
        self.redis_db = redis_db
        self.motlin_token = motlin_token
        self.states_functions = states_functions

    def start(self):
        self.updater.start_polling()

    def handle_users_reply(self, bot, update):

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
            user_state = self.redis_db.get(chat_id).decode("utf-8")

        state_handler = self.states_functions[user_state]
        next_state = state_handler(bot, update, motlin_token=self.motlin_token, redis_db=self.redis_db)
        self.redis_db.set(chat_id, next_state)


def start(bot, update, **kwargs):
    return show_store_menu(bot, update.message.chat_id, kwargs['motlin_token'])


def handle_menu(bot, update, **kwargs):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == str(chat_id):
        return show_products_in_cart(bot, chat_id, kwargs['motlin_token'], query.message.message_id)
    else:
        return show_product_card(bot, chat_id, kwargs['motlin_token'], kwargs['redis_db'], query.data, query.message.message_id)


def handle_description(bot, update, **kwargs):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == str(chat_id):
        return show_products_in_cart(bot, chat_id, kwargs['motlin_token'], query.message.message_id)
    elif query.data == 'HANDLE_MENU':
        return show_store_menu(bot, chat_id, kwargs['motlin_token'], query.message.message_id)
    else:
        return add_product_to_cart(chat_id, kwargs['motlin_token'], kwargs['redis_db'], query.data)


def handle_cart(bot, update, **kwargs):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'HANDLE_MENU':
        return show_store_menu(bot, chat_id, kwargs['motlin_token'], query.message.message_id)
    else:
        delete_product_from_cart(kwargs['motlin_token'], chat_id, query.data)
        return show_products_in_cart(bot, chat_id, kwargs['motlin_token'], query.message.message_id)
