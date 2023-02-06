from contextlib import asynccontextmanager

import aiomysql

from _321CQU.tools import Singleton

from utils.tools.configManager import ConfigReader

__all__ = ['SqlManager']


class SqlManager(metaclass=Singleton):
    def __init__(self):
        # self.connect_args = (str(BASE_DIR) + ConfigReader().get_config('DatabaseConfig', 'path'),)
        self.connect_args = {
            'host': ConfigReader().get_config('DatabaseConfig', 'host'),
            'port': int(ConfigReader().get_config('DatabaseConfig', 'port')),
            'user': ConfigReader().get_config('DatabaseConfig', 'user'),
            'password': ConfigReader().get_config('DatabaseConfig', 'password'),
            'db': ConfigReader().get_config('DatabaseConfig', 'targetDatabase')
        }

    @asynccontextmanager
    async def connect(self) -> aiomysql.Connection:
        async with aiomysql.connect(**self.connect_args) as db:
            try:
                yield db
            except aiomysql.OperationalError as e:
                print("sql error, rollback, info: \n", e)
                await db.rollback()
            finally:
                await db.commit()

    @asynccontextmanager
    async def cursor(self) -> aiomysql.Cursor:
        async with self.connect() as db:
            async with db.cursor() as cursor:
                yield cursor
