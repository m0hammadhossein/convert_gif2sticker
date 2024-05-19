import asyncio
import json
from time import time
from uuid import uuid4

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant

from ConvertGif2Sticker import BASE_DIR


async def check_block(pool, cache, user_id):
    user_id_bytes = str(user_id).encode()  # Convert user_id to bytes for cache lookup
    block_user = await cache.get(user_id_bytes)  # Attempt to retrieve block status from cache

    if block_user is None:
        # If not found in cache, query the database
        async with pool.acquire() as connection:
            block_user = await connection.fetchval('SELECT block FROM users WHERE user_id = $1;', user_id, column=0)
            if block_user is None:
                # If user not in database, insert a new record with block status as False
                await connection.execute('INSERT INTO users VALUES ($1,$2);', user_id, False)
                block_user = b'False'
            else:
                block_user = str(block_user).encode()  # Convert database result to bytes

        # Store the block status in cache for 10 seconds
        await cache.set(user_id_bytes, block_user, 10)

    return block_user == b'True'  # Return True if the user is blocked


# Check if a timer exists for a user and set a new timer if not
async def check_timer(cache, user_id):
    user_id_bytes = f't-{user_id}'.encode()  # Create a cache key for the timer
    timer = await cache.get(user_id_bytes)  # Attempt to retrieve the timer from cache

    if timer is None:
        # If no timer exists, set a new timer to expire in 10 seconds
        dt = str(int(time()) + 10).encode()
        await cache.set(user_id_bytes, dt, 10)
        return

    return int(timer)  # Return the timer value


# Run a subprocess command asynchronously
async def run_subprocess(command: str):
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()  # Execute the command and capture output

    if proc.returncode != 0:
        return False, stderr.decode("utf-8")  # Return False if there was an error

    return True, stdout  # Return True and the output if successful


# Convert a GIF to a WebM sticker
async def convert(path):
    # Prepare the ffprobe command to get video dimensions
    ffprobe_args = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1 -of json "{path}"'
    _, result = await run_subprocess(ffprobe_args)  # Run the ffprobe command
    info = json.loads(result)  # Parse the JSON output
    width = info['streams'][0]['width']  # Get the width of the video
    height = info['streams'][0]['height']  # Get the height of the video
    file_name = BASE_DIR / 'files' / f'{uuid4().hex}.webm'  # Generate a unique file name for the output

    # Determine the resize filter based on video dimensions
    if width < height:
        resize = '-1:512'
    else:
        resize = '512:-1'

    # Run the ffmpeg command to convert the GIF to WebM
    created, res = await run_subprocess(
        f'''ffmpeg -i "{path}" -t 00:02.9 -filter_complex "[0:v]scale={resize}:flags=lanczos,setpts=PTS-STARTPTS,loop=0" -c:v libvpx-vp9 -an -b:v 250k -maxrate 250k -bufsize 250k -auto-alt-ref 0 "{file_name}"'''
    )

    if created:
        return created, file_name  # Return the file name if conversion was successful

    return created, res  # Return the error message if conversion failed


async def check_join_channels(client, user_id, channels):
    for channel in channels.keys():
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                return
        except UserNotParticipant:
            return

    return True
