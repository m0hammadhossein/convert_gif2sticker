from asyncio import sleep, create_task

from pyrogram import Client
from ConvertGif2Sticker.config import API_ID, API_HASH, TOKEN


class ApiBot(Client):
    def __init__(self, pool):
        self.pool = pool
        self.block = dict()
        self.timer = dict()
        self.spam = dict()
        self.channels = dict()

        super().__init__(
            'bot',
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=TOKEN,
            plugins=dict(root='plugins'),
            max_concurrent_transmissions=40
        )

    async def get_channels(self):
        async with self.pool.acquire() as connection:
            rows = await connection.fetch('SELECT * FROM channels;')
            self.channels = {row['channel_id']: [row['title'], row['url']] for row in rows}

    async def set_timer(self, key, seconds, num=None):
        await sleep(seconds)

        try:
            if num == 0:
                del self.spam[key]
            elif num == 1:
                del self.timer[key]
            else:
                del self.block[key]
        except KeyError:
            pass

