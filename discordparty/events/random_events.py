from discord.ext import tasks
from ..utils import utils

import logging

bot = None

users = []

@tasks.loop(seconds=10)
async def random_event_movement_channel():
    for t in list(users):
        user_id = t[0]
        guild_id = t[1]
        guild = bot.get_guild(guild_id)
        user = guild.get_member(user_id)
        if not user.voice:
            # user is no longer in voice remove them
            users.remove(t)
            logging.info('removing user as they are no longer in voice')
            continue
            
        voice = utils.get_random_voice(guild)
        await user.move_to(voice)
    
def add_user(user_id, guild_id):
    users.append((user_id, guild_id,))

def enable_events():
    random_event_movement_channel.start()
    
def set_bot(b):
    global bot
    bot = b