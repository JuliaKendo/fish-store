from telegram.ext import Filters, Updater
from fish_store_lib import get_product_info, get_tg_keyboard, put_into_chart
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
    reply_markup = get_tg_keyboard(kwargs['motlin_token'], 'HANDLE_MENU')
    update.message.reply_text(text='Please choise:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_menu(bot, update, **kwargs):
    query = update.callback_query
    kwargs['redis_db'].set(f'{query.message.chat_id}_chosen_product', query.data)
    product_caption, product_image = get_product_info(kwargs['motlin_token'], query.data)
    reply_markup = get_tg_keyboard(kwargs['motlin_token'], 'HANDLE_DESCRIPTION')
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    bot.send_photo(chat_id=query.message.chat_id,
                   photo=product_image,
                   caption=product_caption,
                   reply_markup=reply_markup)

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update, **kwargs):
    query = update.callback_query
    if query.data == 'HANDLE_MENU':
        reply_markup = get_tg_keyboard(kwargs['motlin_token'], query.data)
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        bot.send_message(chat_id=query.message.chat_id, text="Please choise:", reply_markup=reply_markup)
        return "HANDLE_MENU"
    else:
        chosen_product = kwargs['redis_db'].get(f'{query.message.chat_id}_chosen_product').decode("utf-8")
        if query.data:
            put_into_chart(kwargs['motlin_token'], query.message.chat_id, chosen_product, int(query.data))
        return "HANDLE_DESCRIPTION"
