import os
import redis


class RedisDb(object):

    def __init__(self):
        self.redis_conn = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=os.getenv('REDIS_PORT'),
            db=0, password=os.getenv('REDIS_PASSWORD')
        )

    def set_value(self, key, value):
        self.redis_conn.set(key, value)

    def get_value(self, key):
        return self.redis_conn.get(key).decode("utf-8")
