from contextlib import asynccontextmanager

import aiomysql

from _321CQU.tools import Singleton
from _321CQU.sql_helper import DatabaseConfig

__all__ = ['SqlManager']


class SqlManager(metaclass=Singleton):
    @asynccontextmanager
    async def connect(self) -> aiomysql.Connection:
        async with aiomysql.connect(**DatabaseConfig.Score.config_dict) as db:
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
