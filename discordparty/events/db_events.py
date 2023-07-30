from discord.ext import tasks

from ..db import db

import datetime
import logging

UPDATE_MINUTES = 5

bot = None

@tasks.loop(minutes=UPDATE_MINUTES)
async def deleted_old_mute_events():
    # we want to notify the user if they exceed an hour in chat
    t = int(datetime.datetime.timestamp(datetime.datetime.now()))
    discord_ids = db.get_all_user_muted_expired(t)
    # now go delete all the records
    db.delete_users_muted(discord_ids)

def enable_events():
    logging.info('starting events for db_events')
    deleted_old_mute_events.start()
    
def set_bot(b):
    global bot
    bot = b