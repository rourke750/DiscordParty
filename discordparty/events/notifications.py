from discord.ext import tasks

from ..db import db
from ..utils.utils import get_broadcast_channel

import logging

NOTIFY_MINUTES = 5

bot = None

@tasks.loop(minutes=NOTIFY_MINUTES)
async def notify_hour():
    # we want to notify the user if they exceed an hour in chat
    time_mapping = db.get_current_session_time()
    for discord_id in time_mapping:
        total_minutes = int(time_mapping[discord_id] / 60)
        if total_minutes >= 60 and total_minutes < 60 + NOTIFY_MINUTES:
            # send message 
            user = bot.get_user(discord_id)
            if user is None:
                user = bot.fetch_user(discord_id)
            chan = user.dm_channel
            if chan is None:
                chan = await user.create_dm()
            await chan.send('You have been in voice for %d minutes' % total_minutes)

def enable_events():
    logging.info('starting events for notifications')
    notify_hour.start()
    
def set_bot(b):
    global bot
    bot = b