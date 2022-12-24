import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, has_role


import os
from dotenv import load_dotenv

import asyncio

load_dotenv()



TOKEN = os.getenv("DISCORD_TOKEN")

description = '''Commands to use houseparty features'''

intents = discord.Intents.all()
GLOBAL_GUILDS = {}

bot = commands.Bot(command_prefix='/', description=description, intents=intents)


        
def has_permission_or_role(ctx):
    for r in ctx.author.roles:
        if r.name == 'houseparty-admin':
            return True
    return ctx.author.guild_permissions.administrator

@commands.guild_only()
@bot.command()
@commands.is_owner()
async def sync(ctx, all=False):
    if not all:
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
    else:
        for guild_id in GLOBAL_GUILDS:
            guild = GLOBAL_GUILDS[guild_id]
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
        await bot.tree.sync()
        
@commands.guild_only()
@bot.hybrid_group(name="houseparty", description="admin command", with_app_command=True)
@commands.is_owner()
async def houseparty(ctx):
    await ctx.send("Parent command!")
    
@houseparty.command(name="clear", description="clear all house party related channels", with_app_command=True)
@commands.guild_only()
@commands.check(has_permission_or_role)
async def clear_command(ctx):
    guild = ctx.guild
    # will be global command for configuring but for now just reset guild
    
    broadcasts = discord.utils.get(guild.categories, name=f'broadcast')
    sneak_chat = discord.utils.get(guild.categories, name=f'sneak')
    notifications_chat = discord.utils.get(guild.categories, name=f'notifications')
    private_channels = discord.utils.get(guild.categories, name=f'private_house_channel')
    delete_sub_channels_and_category(guild, [broadcasts, sneak_chat, notifications_chat, private_channels])
    
    await ctx.send('Finished Deleting channels')
    
@houseparty.command(name="create", description="create all house party related channels", with_app_command=True)
@commands.guild_only()
@commands.check(has_permission_or_role)
async def create_command(ctx):
    guild = ctx.guild
    await setup_guild(guild)
    await ctx.send('Finished creating channels, roles, and categories')
    
def delete_sub_channels_and_category(guild, categories):
    channels = []
    for cat in categories:
        for chan in cat.channels:
            channels.append(chan.delete())
        channels.append(cat.delete())
    asyncio.gather(*channels)
            

@commands.guild_only()
@houseparty.command(name="private", description="Command to lock your channel with the people inside", with_app_command=True)
async def private(ctx: commands.Context):
    guild = GLOBAL_GUILDS[ctx.guild.id]
    user_id = ctx.author.id
    member = guild.get_member(user_id)
    v = member.voice
    if v is None:
        await ctx.send('You must be in a channel')
        return
    c = v.channel
    # if player in channel want to do 2 things
    # 1. give everyone in channel role
    # 2. set channel role
    role = await guild.create_role(name=f'{member.name}-PrivateRole')
    house_party_role = discord.utils.get(guild.roles, name=f'houseparty')
    category = discord.utils.get(guild.categories, name=f'private_house_channel')
    perms = {'speak': True, 'view_channel': True, 'connect': True, 'use_voice_activation': True, }
    overwrite = discord.PermissionOverwrite(**perms)
    bot_account = discord.PermissionOverwrite(**{'speak': False, 'view_channel': True, 'connect': True})
    new_channel = await guild.create_voice_channel(name=f'{member.name}-PrivateRole', category=category, overwrites={role: overwrite, house_party_role: bot_account})
    #await new_channel.set_permissions(role, reason='Temp private channel', overwrite=overwrite)
    
    # set the private_house_party_role so we can delete this later
    private_house_role = discord.utils.get(guild.roles, name='private_house_party_role')
    overwrite = discord.PermissionOverwrite()
    await new_channel.set_permissions(private_house_role, reason='Temp role for deleting channel when done', overwrite=overwrite)
    
    # iterate through channel members and set role then move
    tasks = []
    for member in c.members:
        #await member.add_roles(role)
        #await member.move_to(new_channel)
        tasks.append(member.add_roles(role))
        tasks.append(member.move_to(new_channel))
    await asyncio.gather(*tasks)
    
    await ctx.send('Locking channel')
    
@create_command.error
@clear_command.error
async def command_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send('Only the owner of this bot can run this command')
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole) or isinstance(error, commands.CheckFailure):
        await ctx.send('You have to be an admin or have the role houseparty-admin')
    else:
        print(error)

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
    
async def setup_guild(guild):
    await create_roles_for_guild(guild) # create roles for guild 
    await create_categories_for_guild(guild)
    await create_default_channels_for_guild(guild)
        
async def create_categories_for_guild(guild):
    priv_chat = discord.utils.get(guild.categories, name=f'private_house_channel')
    if priv_chat is None:
        house_party_role = role = discord.utils.get(guild.roles, name=f'houseparty')
        bot_account = discord.PermissionOverwrite(**{'speak': True, 'view_channel': True, 'connect': True, 'manage_channels': True})
        perms = {'speak': True, 'view_channel': True, 'connect': False}
        overwrite = discord.PermissionOverwrite(**perms)
        priv_chat = await guild.create_category("private_house_channel", overwrites={guild.default_role: overwrite, house_party_role: bot_account}, reason=None)
        
    sneak_chat = discord.utils.get(guild.categories, name=f'sneak')
    if sneak_chat is None:
        perms = {'speak': True, 'view_channel': True, 'connect': True}
        overwrite = discord.PermissionOverwrite(**perms)
        sneak_chat = await guild.create_category("sneak", overwrites={guild.default_role: overwrite}, reason=None)
        
    broadcast_chat = discord.utils.get(guild.categories, name=f'broadcast')
    if broadcast_chat is None:
        perms = {'speak': True, 'view_channel': True, 'connect': True}
        overwrite = discord.PermissionOverwrite(**perms)
        broadcast_chat = await guild.create_category("broadcast", overwrites={guild.default_role: overwrite}, reason=None)
        
    notification_chat = discord.utils.get(guild.categories, name='notifications')
    if notification_chat is None:
        perms = {'view_channel': True, 'read_messages': True}
        overwrite = discord.PermissionOverwrite(**perms)
        notification_chat = await guild.create_category("notifications", overwrites={guild.default_role: overwrite}, reason=None)

async def create_roles_for_guild(guild):
    #role = discord.utils.get(guild.roles, name=f'default')
    #if role is None:
    #    role = await guild.create_role(name=f'default')
    #    perms = {'speak': True, 'view_channel': True, 'connect': False}
    # remove the everyone permissions and set to none
    #await guild.default_role.edit(permissions=perms = {'speak': True, 'view_channel': True, 'connect': False})
    private_house_role = discord.utils.get(guild.roles, name=f'private_house_party_role')
    if private_house_role is None:
        private_house_role = await guild.create_role(name=f'private_house_party_role')
        
    admin_role = discord.utils.get(guild.roles, name=f'houseparty-admin')
    if admin_role is None:
        admin_role = await guild.create_role(name=f'houseparty-admin')
        
async def create_default_channels_for_guild(guild):
    channel = discord.utils.get(guild.channels, name=f'house-party')
    if channel is None:
        broadcast_chat = discord.utils.get(guild.categories, name=f'broadcast')
        channel = await guild.create_voice_channel('house-party', category=broadcast_chat)
        
    sneak = discord.utils.get(guild.channels, name=f'sneak-party')
    if sneak is None:
        sneak_chat = discord.utils.get(guild.categories, name=f'sneak')
        sneak = await guild.create_voice_channel('sneak-party', category=sneak_chat)
        
    notifications = discord.utils.get(guild.channels, name=f'who-is-in-the-house')
    if notifications is None:
        notifications_chat = discord.utils.get(guild.categories, name=f'notifications')
        notifications = await guild.create_text_channel('who-is-in-the-house', category=notifications_chat)
    
async def handle_multi_house_channel(guild_id):
    # this function will handle generating multiple broadcast channels if each one has someone in one
    guild = GLOBAL_GUILDS[guild_id]
    broadcast_chat = discord.utils.get(guild.categories, name=f'broadcast')
    channel = await guild.create_voice_channel('house-party', category=broadcast_chat)
    
async def remove_zero_house_channel(chan):
    # check if there is more than one guild channel and if there is delete this
    guild = GLOBAL_GUILDS[chan.guild.id]
    broadcast_chat = discord.utils.get(guild.categories, name=f'broadcast')
    channels = None
    for cat_tuple in guild.by_category():
        if cat_tuple[0] is None:
            continue
        if broadcast_chat.id == cat_tuple[0].id:
            channels = cat_tuple[1]
            break
    if len(channels) > 1:
        await chan.delete()
    
    
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
    
# todo when someone joins a broadcast channel and there are none with the broadcast categroy that are empty create a new one
bot.run(TOKEN)