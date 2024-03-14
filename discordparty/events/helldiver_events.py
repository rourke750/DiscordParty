from discord.ext import tasks
from ..utils import utils

import logging
from ..db import db

import asyncio
import requests
import traceback 
import re

bot = None

REGEX_PAGE = r"(^.*Mission Win Rate:.*$)"

REGEX_STATS = r"Mission Win Rate: ([\d]+%).+Bug Kills: (\d+.\d+ \S).+Bot Kills: (\d+.\d+ \S).+Bullet Acc : (\d+%).+Deaths: (\d+.\d+ \S).+Team Kills: (\d+.\d+ \S).+$"

CHANNEL_PREFIX = {
    1: 'Mission Win Rate: ',
    2: 'Bug Kills: ',
    3: 'Bot Kills: ',
    4: 'Bullet Acc: ',
    5: 'Deaths: ',
    6: 'Team Kills: '
}

def fetch_stats():
    page_details = requests.get('https://helldivers.io/')
    match = re.search(REGEX_PAGE, page_details.text, re.MULTILINE)
    stats = match.group()
    stats_match = re.search(REGEX_STATS, stats, re.MULTILINE)
    return stats_match.groups()

@tasks.loop(minutes=10)
async def find_hell_divers_stats():
    try:
        data = db.get_hell_diver_channels()
        if len(data) > 0:
            stats = fetch_stats()
        for guild_data in data:
            guild_id = guild_data[0]
            guild = bot.get_guild(guild_id)
            
            edits = []
            for i in range(1, 7):
                chan = guild.get_channel(guild_data[i])
                new_name = CHANNEL_PREFIX[i] + stats[i-1]
                edits.append(chan.edit(name=new_name))
            await asyncio.gather(*edits)
            
    except Exception as e:
        print(e)
        logging.error(e)
        traceback.print_exc() 

def enable_events():
    logging.info('starting events for hell divers')
    find_hell_divers_stats.start()
    
def set_bot(b):
    global bot
    bot = b