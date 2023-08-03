import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, has_role

from .commands import DiscordPartyCommands
from .commands import get_help_message
from .utils.utils import *
from .mappings.mapping import DRole
from .db import db
from .events import events
from .views import views

import os
from dotenv import load_dotenv
import datetime
import logging

import asyncio

load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

description = '''Commands to use houseparty features'''

intents = discord.Intents.all()

discord.utils.setup_logging(level=logging.INFO)

bot = commands.Bot(command_prefix='/', description=description, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(bot.guilds)
    
    tasks = []
    for guild in bot.guilds:
        #GLOBAL_GUILDS[guild.id] = guild
        tasks.append(setup_guild(guild, bot))
    await asyncio.gather(*tasks)
    events.enable_events()
        
@bot.event
async def on_guild_join(guild):
    #GLOBAL_GUILDS[guild.id] = guild
    await setup_guild(guild, bot)
    
def should_broadcast(roles):
    for role in roles:
        if role.name == DRole.BROADCAST_DELETE_ROLE.value:
            return 2
        elif role.name == DRole.BROADCAST_ROLE.value:
            return 1
    return 0

 
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
        if cat is not None and cat.name == 'private_house_channel':
            bot_role = getBotMainRole(member.guild, bot)
            for r in voice_chan_before.overwrites:
                if type(r) is discord.Role and r.name != 'private_house_party_role' and r.name != '@everyone' and r.name != bot_role.name:
                    await r.delete()
            await voice_chan_before.delete()
    
    chan = get_broadcast_channel(member.guild)
    if voice_chan_after is not None: 
        # Handle case where someone joined a channel that broadcasts
        # check if category exists
        # now get the permissions for the category
        broadCastVal = should_broadcast(voice_chan_after.changed_roles)
        if broadCastVal == 0 and voice_chan_after.category is not None:
            broadCastVal = should_broadcast(voice_chan_after.category.changed_roles)
        if broadCastVal > 0: 
            # we want to broadcast
            members_len = len(voice_chan_after.members)
            if members_len == 0:
                return
            if members_len > 1:
                members = ', '.join([x.name for x in voice_chan_after.members])
                await chan.send(f'{members} are in the house together')
            else:
                role_name = '@everyone'
                db_role_id = db.get_guild_broadcast_role(voice_chan_after.guild.id)
                if db_role_id is not None:
                    role_name = voice_chan_after.guild.get_role(db_role_id).mention
                    print(role_name)
                await chan.send(f'{voice_chan_after.members[0].name} has entered the chat {role_name}')
                # check if we need to create a new channel
                if broadCastVal == 2:
                    await handle_multi_house_channel(member.guild)
            # now lets track the persons time, need to make sure previous voice channel was not a broadcast
            #not_previous_tracked = voice_chan_before is not None and voice_chan_before.category is not None and not should_broadcast(voice_chan_before.category.changed_roles) > 0
            #not_in_previous_channel = voice_chan_before is None or voice_chan_before.category is None
            #if not_in_previous_channel or not_previous_tracked:
        if voice_chan_before is None:
            db.insert_time(member.id, datetime.datetime.timestamp(datetime.datetime.now()))
                
        
    if voice_chan_before is not None:
        # handle case where we want to delete too many channels
        if voice_chan_after is None:
            db.update_end_time(member.id, datetime.datetime.timestamp(datetime.datetime.now()))
        cat = voice_chan_before.category
        if cat is None:
            return
        if should_broadcast(cat.changed_roles) == 2: # if we are greater than zero than they came from a voice channel we are tracking
            members_len = len(voice_chan_before.members)
            if members_len == 0:
                await remove_zero_house_channel(voice_chan_before)
                
#@bot.event
async def on_message(message):
    #handle messages being sent to user
    if message.guild is not None or message.author.bot:
        return
        
    content = message.content
    if content == 'help':
        # print help message
        await message.channel.send(content=get_help_message())
    elif content == 'mute':
        await message.channel.send(view=views.SupressWave(message.author.id))
    else:
        await message.channel.send(content='type help for help')
    
        

asyncio.run(bot.add_cog(DiscordPartyCommands(bot)))
events.set_bot(bot)
bot.run(TOKEN)