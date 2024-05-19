from html import escape

from asyncpg import UniqueViolationError
from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import UserIsBlocked, ChannelPrivate
from pyrogram.types import Message

from ConvertGif2Sticker.client import ApiBot
from ConvertGif2Sticker.config import ADMIN, MESSAGES


@ApiBot.on_message(
    filters.user(ADMIN)
    & filters.text
    & filters.regex(r'^/(block|unblock) (\d+|@[a-zA-Z0-9_]+)$')
)
async def manage_user(bot: ApiBot, msg: Message):
    language_code = msg.from_user.language_code
    action, user = msg.matches[0].groups()

    if language_code != 'fa':
        language_code = 'en'

    information = await bot.get_users(user)
    user_language_code = information.language_code
    user_id = information.id

    if user_language_code != 'fa':
        user_language_code = 'en'

    async with bot.pool.acquire() as connection:
        if action == 'block':
            res = await connection.fetchrow(
                'UPDATE users SET block = TRUE WHERE user_id = $1 AND NOT block RETURNING user_id;', user_id
            )

            if res is None:
                await msg.reply_text(MESSAGES[language_code]['already_blocked'])
            else:
                await msg.reply_text(MESSAGES[language_code]['blocked'])

                try:
                    await bot.send_message(user_id, MESSAGES[user_language_code]['block'])
                except UserIsBlocked:
                    pass
        else:
            res = await connection.fetchrow(
                'UPDATE users SET block = FALSE WHERE user_id = $1 AND block RETURNING user_id;', user_id
            )

            if res is None:
                await msg.reply_text(MESSAGES[language_code]['already_unblocked'])
            else:
                await msg.reply_text(MESSAGES[language_code]['unblocked'])

                try:
                    await bot.send_message(user_id, MESSAGES[user_language_code]['unblock'])
                except UserIsBlocked:
                    pass


@ApiBot.on_message(
    filters.user(ADMIN)
    & filters.text
    & filters.regex(r'^/add (\-\d+) (https?:\/\/t\.me\/\+?[a-zA-Z0-9_\-]+)$')
)
async def add_channel(bot: ApiBot, msg: Message):
    channel_id, url = msg.matches[0].groups()
    language_code = msg.from_user.language_code

    if language_code != 'fa':
        language_code = 'en'

    try:
        chat_info = await bot.get_chat(channel_id)
    except ChannelPrivate:
        await msg.reply_text(MESSAGES[language_code]['not_found_channel'])
        return

    if chat_info.type != ChatType.CHANNEL:
        await msg.reply_text(MESSAGES[language_code]['error_channel'])
        return

    async with bot.pool.acquire() as connection:
        try:
            await connection.execute('INSERT INTO channels VALUES ($1, $2, $3);', chat_info.id, chat_info.title, url)
        except UniqueViolationError:
            await msg.reply_text(MESSAGES[language_code]['exists_channel'])
            return

        bot.channels[chat_info.id] = [chat_info.title, url]
        await msg.reply_text(MESSAGES[language_code]['add_channel'])


@ApiBot.on_message(
    filters.user(ADMIN)
    & filters.text
    & filters.regex(r'^/remove (\-\d+)$')
)
async def remove_channel(bot: ApiBot, msg: Message):
    channel_id = int(msg.matches[0].group(1))
    language_code = msg.from_user.language_code

    if language_code != 'fa':
        language_code = 'en'

    async with bot.pool.acquire() as connection:
        res = await connection.fetchrow('DELETE FROM channels WHERE channel_id = $1 RETURNING channel_id;', channel_id)

        if res is None:
            await msg.reply_text(MESSAGES[language_code]['not_exists_channel'])
        else:
            del bot.channels[channel_id]
            await msg.reply_text(MESSAGES[language_code]['remove_channel'])


@ApiBot.on_message(filters.user(ADMIN) & filters.command('channels'))
async def get_channels(bot: ApiBot, msg: Message):
    language_code = msg.from_user.language_code

    if language_code != 'fa':
        language_code = 'en'

    if not bot.channels:
        await msg.reply_text(MESSAGES[language_code]['empty_channels'])
        return

    txt = '\n'.join([f'<code>{row[0]}</code> : {escape(row[1])}' for row in bot.channels])
    await msg.reply_text(txt, parse_mode=ParseMode.HTML)
