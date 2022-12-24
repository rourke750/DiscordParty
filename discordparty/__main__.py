import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, has_role

from .commands import DiscordPartyCommands
from .utils.utils import *

import os
from dotenv import load_dotenv

import asyncio

load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

description = '''Commands to use houseparty features'''

intents = discord.Intents.all()
GLOBAL_GUILDS = {}

bot = commands.Bot(command_prefix='/', description=description, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(bot.guilds)
    
    tasks = []
    for guild in bot.guilds:
        GLOBAL_GUILDS[guild.id] = guild
        tasks.append(setup_guild(guild))
    await asyncio.gather(*tasks)
        
@bot.event
async def on_guild_join(guild):
    GLOBAL_GUILDS[guild.id] = guild
    await setup_guild(guild)
    
    
@bot.event
async def on_voice_state_update(member, before, after):
    user_name = member.name
    voice_chan_after = after.channel
    voice_chan_before = before.channel
    
    if voice_chan_before is not None and voice_chan_after is not None and voice_chan_before.id == voice_chan_after.id:
        return
        
    # check for if we need to delete a private channel
    if voice_chan_before is not None and len(voice_chan_before.members) == 0 and voice_chan_before is not None:
        # check category if it is a private chat
        cat = voice_chan_before.category
        if cat is None:
            return
        if cat.name == 'private_house_channel':
            for r in voice_chan_before.overwrites:
                if type(r) is discord.Role and r.name != 'private_house_party_role' and r.name != '@everyone' and r.name != 'houseparty':
                    await r.delete()
            await voice_chan_before.delete()
    
    chan = discord.utils.get(member.guild.channels, name=f'who-is-in-the-house')
    if voice_chan_after is not None: 
        # Handle case where someone joined a channel that broadcasts
        # check if category exists
        cat = voice_chan_after.category
        if cat is None:
            return
        if cat.name == 'broadcast': # we want to broadcast
            members_len = len(voice_chan_after.members)
            if members_len == 0:
                return
            if members_len > 1:
                members = ', '.join([x.name for x in voice_chan_after.members])
                await chan.send(f'{members} are in the house together')
            else:
                await chan.send(f'{voice_chan_after.members[0].name} has entered the chat @everyone')
                await handle_multi_house_channel(member.guild.id)
                pass
    if voice_chan_before is not None:
        # handle case where we want to delete too many channels
        cat = voice_chan_before.category
        if cat is None:
            return
        if cat.name == 'broadcast': # we want to broadcast
            members_len = len(voice_chan_before.members)
            if members_len == 0:
                await remove_zero_house_channel(voice_chan_before)
    
asyncio.run(bot.add_cog(DiscordPartyCommands(bot)))
bot.run(TOKEN)