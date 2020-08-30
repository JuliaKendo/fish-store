import fish_store_lib
from telegram.ext import Filters, Updater
from telegram import InlineKeyboardMarkup
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

        next_state = state_handler(bot, update, self.motlin_token)
        self.redis_db.set(chat_id, next_state)


def start(bot, update, motlin_token):

    keyboard = fish_store_lib.get_tg_keyboard(motlin_token)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='Please choise:', reply_markup=reply_markup)
    return "BUTTON"


def button(bot, update, motlin_token):
    query = update.callback_query

    bot.edit_message_text(text="Selected option: {}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    return "START"
