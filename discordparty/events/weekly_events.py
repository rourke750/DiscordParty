from discord.ext import tasks
from ..utils import utils
from ..db import db

import datetime
import logging

bot = None

time = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)

@tasks.loop(time=time)
async def reset_tokens():
    logging.info('Resetting all users tokens')
    db.reset_all_users_tokens()
    logging.info('Users tokens have been reset')

def enable_events():
    reset_tokens.start()
    
def set_bot(b):
    global bot
    bot = b