import discord

from ..mappings.mapping import DRole

import asyncio
import random

async def setup_guild(guild, bot):
    await create_roles_for_guild(guild) # create roles for guild 
    await create_categories_for_guild(guild, bot)
    await create_default_channels_for_guild(guild)
        
async def create_categories_for_guild(guild, bot):
    priv_chat = discord.utils.get(guild.categories, name=f'private_house_channel')
    if priv_chat is None:
        house_party_role = get_bot_role(bot, guild)
        if house_party_role is None:
            print("error no bot default role")
        bot_account = discord.PermissionOverwrite(**{'speak': True, 'view_channel': True, 'connect': True, 'manage_channels': True})
        overwrite = discord.PermissionOverwrite(**{'speak': True, 'view_channel': True, 'connect': False})
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
        broadcast_delete_role = discord.utils.get(guild.roles, name=DRole.BROADCAST_DELETE_ROLE.value)
        broadcast_chat = await guild.create_category('broadcast', overwrites={guild.default_role: overwrite, broadcast_delete_role: overwrite}, reason=None)
        
    # handle if broadcast_chat wasnt generated a role from earlier version
    broadcast_delete_role = discord.utils.get(guild.roles, name=DRole.BROADCAST_DELETE_ROLE.value)
    if broadcast_delete_role not in broadcast_chat.overwrites:
        perms = {'speak': True, 'view_channel': True, 'connect': True}
        overwrite = discord.PermissionOverwrite(**perms)
        await broadcast_chat.set_permissions(broadcast_delete_role, overwrite=overwrite)
        
    notification_chat = discord.utils.get(guild.categories, name='notifications')
    if notification_chat is None:
        perms = {'view_channel': True, 'read_messages': True}
        overwrite = discord.PermissionOverwrite(**perms)
        notification_chat = await guild.create_category("notifications", overwrites={guild.default_role: overwrite}, reason=None)

async def create_roles_for_guild(guild):
    private_house_role = discord.utils.get(guild.roles, name=DRole.PRIVATE_ROLE.value)
    if private_house_role is None:
        private_house_role = await guild.create_role(name=DRole.PRIVATE_ROLE.value)
        
    admin_role = discord.utils.get(guild.roles, name=DRole.ADMIN_ROLE.value)
    if admin_role is None:
        admin_role = await guild.create_role(name=DRole.ADMIN_ROLE.value)
        
    # let's create two new roles 1 for broadcasts and one if channel should be deleted if no one in channel
    if discord.utils.get(guild.roles, name=DRole.BROADCAST_ROLE.value) is None:
        await guild.create_role(name=DRole.BROADCAST_ROLE.value)
        
    if discord.utils.get(guild.roles, name=DRole.BROADCAST_DELETE_ROLE.value) is None:
        await guild.create_role(name=DRole.BROADCAST_DELETE_ROLE.value)
        
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
    
async def handle_multi_house_channel(guild):
    # this function will handle generating multiple broadcast channels if each one has someone in one
    #guild = GLOBAL_GUILDS[guild_id]
    broadcast_chat = discord.utils.get(guild.categories, name=f'broadcast')
    channel = await guild.create_voice_channel('house-party', category=broadcast_chat)
    
async def remove_zero_house_channel(chan):
    # check if there is more than one guild channel and if there is delete this
    guild = chan.guild
    broadcast_chat = discord.utils.get(guild.categories, name=f'broadcast')
    channels = None
    if chan.category is not None:
        channels = chan.category.channels
    if len(channels) > 1:
        await chan.delete()
        
def get_broadcast_channel(guild):
    return discord.utils.get(guild.channels, name=f'who-is-in-the-house')
        
def delete_sub_channels_and_category(guild, categories):
    channels = []
    for cat in categories:
        for chan in cat.channels:
            channels.append(chan.delete())
        channels.append(cat.delete())
    asyncio.gather(*channels)
    
def get_bot_role(bot, guild):
    house_party_roles = guild.get_member(bot.user.id).roles
    for bot_role in house_party_roles:
        if bot_role.is_bot_managed() and len(bot_role.members) == 1 and bot.user.id == bot_role.members[0].id:
            return bot_role
    return None
            
def get_random_voice(guild):
    channels = guild.voice_channels
    i = random.randrange(0, len(channels))
    return channels[i]
    
def get_user_obj_id_or_name(guild, val):
    if val.isnumeric():
        return guild.get_member(int(val))
    return discord.utils.get(guild.members, display_name=val)