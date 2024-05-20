import asyncpg
import uvloop
from pyrogram import idle

from ConvertGif2Sticker.client import ApiBot
from ConvertGif2Sticker.config import DB_USER, DB_PASSWORD, DB_PORT, DB_NAME
from ConvertGif2Sticker.database import create_tables


async def main():
    pool = await asyncpg.create_pool(
        host='127.0.0.1',
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        max_size=100
    )
    await create_tables(pool)
    client = ApiBot(pool)
    await client.get_channels()
    await client.start()
    await idle()
    await client.stop()
    await pool.close()
    await cache.close()


uvloop.run(main())
