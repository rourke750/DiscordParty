import discord

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