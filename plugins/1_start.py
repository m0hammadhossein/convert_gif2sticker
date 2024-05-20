from asyncio import create_task
from os import remove
from uuid import uuid4

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.errors import UserIsBlocked
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from ConvertGif2Sticker.client import ApiBot
from ConvertGif2Sticker.config import MESSAGES, ADMIN
from ConvertGif2Sticker.functions import check_block, convert, check_timer, check_join_channels


@ApiBot.on_message(~filters.user(ADMIN) & filters.private, group=-1)
async def check_spam(bot: ApiBot, msg: Message):
    user_id = msg.from_user.id
    is_block = await check_block(bot, user_id)

    if is_block:
        await msg.stop_propagation()

    cn_msg = bot.spam.get(user_id)

    if cn_msg is None:
        bot.spam[user_id] = 1
        create_task(bot.set_timer(user_id, 5, 0))
        return

    bot.spam[user_id] += 1

    if cn_msg == 5:
        language_code = msg.from_user.language_code
        if language_code != 'fa':
            language_code = 'en'

        async with bot.pool.acquire() as connection:
            await connection.execute('UPDATE users SET block = TRUE WHERE user_id = $1;', user_id)
            await msg.reply_text(MESSAGES[language_code]['spam_block'], parse_mode=ParseMode.HTML)
            await msg.stop_propagation()


@ApiBot.on_message(filters.private & filters.command('start'))
async def start(bot, msg: Message):
    language_code = msg.from_user.language_code

    if language_code != 'fa':
        language_code = 'en'

    await msg.reply(MESSAGES[language_code]['start'], parse_mode=ParseMode.HTML)


@ApiBot.on_message(filters.private & filters.animation)
async def create_file(bot: ApiBot, msg: Message):
    user_id = msg.from_user.id
    language_code = msg.from_user.language_code
    now_time = msg.date.timestamp()

    if language_code != 'fa':
        language_code = 'en'

    timer = await check_timer(bot, user_id, now_time)

    if timer is not None:
        wait_time = int(timer - now_time)
        await msg.reply_text(MESSAGES[language_code]['wait'].format(wait_time))
        return

    is_joined = await check_join_channels(bot, user_id, bot.channels)

    if not is_joined:
        keyboard = [[InlineKeyboardButton(channel[0], url=channel[1])] for channel in bot.channels.values()]
        await msg.reply_text(MESSAGES[language_code]['join_channel'], reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if msg.animation.duration > 3:
        await msg.reply(MESSAGES[language_code]['error_gif_duration'])
        return

    await msg.reply_text(MESSAGES[language_code]['wait_for_convert'])
    animation_path = await msg.download(uuid4().hex)
    created, res = await convert(animation_path)

    try:
        if created:
            await msg.reply_document(res)
        else:
            await msg.reply_text(res)
    except UserIsBlocked:
        pass

    remove(animation_path)
    remove(res)
