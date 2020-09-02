import os
import redis
import tg_bot
from dotenv import load_dotenv
from fish_store_lib import get_moltin_access_token


def main():
    load_dotenv()

    moltin_token = get_moltin_access_token(
        client_secret=os.getenv('MOLTIN_CLIENT_SECRET'),
        client_id=os.getenv('MOLTIN_CLIENT_ID')
    )

    redis_conn = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        db=0, password=os.getenv('REDIS_PASSWORD')
    )
    redis_conn.flushdb()

    states_functions = {
        'START': tg_bot.start,
        'HANDLE_MENU': tg_bot.handle_menu,
        'HANDLE_DESCRIPTION': tg_bot.handle_description,
        'HANDLE_CART': tg_bot.handle_cart
    }

    bot = tg_bot.TgDialogBot(
        os.getenv('TG_ACCESS_TOKEN'),
        moltin_token,
        redis_conn,
        states_functions
    )
    bot.start()


if __name__ == '__main__':
    main()
