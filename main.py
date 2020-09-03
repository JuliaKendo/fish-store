import os
import tg_bot
from dotenv import load_dotenv


def main():
    load_dotenv()

    states_functions = {
        'START': tg_bot.start,
        'HANDLE_MENU': tg_bot.handle_menu,
        'HANDLE_DESCRIPTION': tg_bot.handle_description,
        'HANDLE_CART': tg_bot.handle_cart,
        'WAITING_EMAIL': tg_bot.waiting_email
    }

    connections_params = {
        'REDIS_HOST': os.getenv('REDIS_HOST'),
        'REDIS_PORT': os.getenv('REDIS_PORT'),
        'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
        'MOLTIN_CLIENT_ID': os.getenv('MOLTIN_CLIENT_ID'),
        'MOLTIN_CLIENT_SECRET': os.getenv('MOLTIN_CLIENT_SECRET')
    }

    bot = tg_bot.TgDialogBot(
        os.getenv('TG_ACCESS_TOKEN'),
        states_functions,
        connections_params
    )
    bot.start()


if __name__ == '__main__':
    main()
