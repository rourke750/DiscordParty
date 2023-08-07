from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, has_role, EmojiConverter

from typing import Literal, Union

from .mappings.mapping import DRole
from .utils.utils import *
from .utils.checks import *
from .utils import quiz, reactions
from .db import db
from .views import views

import logging
import emoji as emoji_p
import datetime

import asyncio

def get_help_message():
    return '''
            List of commands:
            mute: returns a view for modifying mute of axillary notifications
           '''

class DiscordPartyCommands(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def sync_chatparty(self, ctx, all=False):
        await self.sync(ctx, all)

    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx, all=False):
        if not all:
            logging.info('sync command run for just this guild')
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
            self.bot.tree.copy_global_to(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
        else:
            logging.info('sync command run for all guilds')
            for guild in self.bot.guilds:
                self.bot.tree.clear_commands(guild=guild)
                await self.bot.tree.sync(guild=guild)
            await self.bot.tree.sync()
            
    @commands.guild_only()
    @commands.hybrid_group(name="chatparty", description="admin command", with_app_command=True)
    async def chatparty(self, ctx):
        await ctx.send("Parent command!")
        
    @commands.guild_only()
    @commands.hybrid_group(name="chatpartyadmin", description="admin command", with_app_command=True)
    @app_commands.default_permissions(manage_guild=True)
    async def chatpartyadmin(self, ctx):
        await ctx.send("Parent command!")
        
    @commands.guild_only()
    @chatparty.command(name="time", description="Command to get all time this week", with_app_command=True)
    async def time(self, ctx: commands.Context, current=False):
        user_id = ctx.author.id
        end = int(datetime.datetime.timestamp(datetime.datetime.now()))
        current_week = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sub = current_week - datetime.timedelta(days=datetime.datetime.now().weekday(), hours=0, minutes=0, seconds=0)
        start = int(datetime.datetime.timestamp(sub))
        total_time = db.get_total_active_time_minutes(user_id, start, end)
        if not current:
            total_time = total_time + db.get_arcival_time_minutes(user_id, sub)
            await ctx.send('Time since Monday %d minutes' % total_time)
        else:
            await ctx.send('Current time in voice %d minutes' % total_time)
            
    @commands.guild_only()
    @chatparty.command(name="wave", description="Command to wave to another user and get them to join", with_app_command=True)
    async def wave(self, ctx: commands.Context, user: discord.Member):
        command_user = ctx.author
        # check if the user is in a voice channel
        if command_user.voice is None or command_user.voice.channel is None:
            await ctx.send('You must be in a voice channel to run this command', ephemeral=True)
            return
            
        # check if the user we are waving to is muted
        if db.get_user_muted(user.id) is not None:
            await ctx.send('%s is muted, can\'t send wave' % user.display_name, ephemeral=True)
            return
            
        jump_url = command_user.voice.channel.jump_url
        await ctx.send('Waved to %s' % user.display_name, ephemeral=True)
        user_channel = user.dm_channel
        if user_channel is None:
            user_channel = await user.create_dm()
        await user_channel.send('%s waved to you %s' % (command_user.display_name, jump_url), view=views.SupressWave(user.id))
        
    @commands.guild_only()
    @chatpartyadmin.command(name="broadcast", description="Set channel to allow broadcasts from", with_app_command=True)
    @commands.check(has_permission_or_role)
    async def broadcast(self, ctx, set: Literal['set', 'unset'], channel: discord.VoiceChannel):
        broadcast_role = discord.utils.get(ctx.guild.roles, name=DRole.BROADCAST_ROLE.value)
        if broadcast_role not in channel.overwrites:
            perms = {'speak': True, 'view_channel': True, 'connect': True}
            overwrite = discord.PermissionOverwrite(**perms)
            await channel.set_permissions(broadcast_role, overwrite=overwrite)
            await ctx.send("Added channel to broadcast!")
        else:
            await ctx.send("Channel is already added")
        
    @commands.guild_only()
    @chatpartyadmin.group(name="refresh", description="allow refreshing of channels", with_app_command=True)
    @commands.check(has_permission_or_role)
    async def refresh(self, ctx):
        await ctx.send("Parent command!")
        
    @commands.guild_only()
    @chatpartyadmin.group(name="config", description="allow modifying chat party configuration", with_app_command=True)
    @commands.check(has_permission_or_role)
    async def config(self, ctx):
        await ctx.send("Parent command!")
        
    @config.command(name="role_create", description="Command for creating role message in current channel", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def create_role_message(self, ctx):
        # check if the guild already has a role message
        message_id = db.get_message_id_for_guild(ctx.guild.id)
        if message_id is not None:
            # message is is already present
            await ctx.send("Role message already exists for this guild", ephemeral=True)
            return
        # let's create it
        message = await ctx.send("MessageRoles, like the roles below to be added")
        reactions.track_new_message_id(message.id, ctx.guild.id)
        # lets try disable adding roles to messages for this channel
        house_party_role = get_bot_role(self.bot, ctx.guild)
        tasks = []
        tasks.append(ctx.channel.set_permissions(house_party_role, add_reactions=True))
        tasks.append(ctx.channel.set_permissions(ctx.guild.default_role, add_reactions=False))
        await asyncio.gather(*tasks)
        
    @config.command(name="role_delete", description="Command for deleting role message", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def remove_role_message(self, ctx):
        # check if the guild already has a role message
        message_id = db.get_message_id_for_guild(ctx.guild.id)
        if message_id is None:
            # message is is already present
            await ctx.send("Role message does not exist for this guild", ephemeral=True)
            return
        # let's untrack it
        reactions.untrack_message_id(message_id)
        # lets delete it now
        message = await ctx.fetch_message(message_id)
        await message.delete()
        await ctx.send("Message role deleted", ephemeral=True)
        
    @config.command(name="role_add_reaction", description="Command to add role to role message", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def create_role_reaction(self, ctx, emoji:str, description:str, role: discord.Role):
        # check if a message is set
        message_id = db.get_message_id_for_guild(ctx.guild.id)
        if message_id is None:
            await ctx.send("You do not have a roles message created", ephemeral=True)
            return
        v_unicode = emoji_p.demojize(emoji)
        if v_unicode == emoji:
            await ctx.send("Please only use emojis in emoji field", ephemeral=True)
            return
        message = await ctx.fetch_message(message_id)
        if message is None:
            await ctx.send("Error, the roles message doesn't exist", ephemeral=True)
        success = await reactions.add_emoji_with_description(message, emoji, description, role)
        if not success:
            # the emoji is already present
            await ctx.send("That emoji is already being used", ephemeral=True)
        else:
            await ctx.send("Added role reaction", ephemeral=True)
            
    @config.command(name="role_remove_reaction", description="Command to remove role from role message", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def remove_role_reaction(self, ctx, emoji:str):
        message_id = db.get_message_id_for_guild(ctx.guild.id)
        if message_id is None:
            await ctx.send("You do not have a roles message created", ephemeral=True)
            return
        v_unicode = emoji_p.demojize(emoji)
        if v_unicode == emoji:
            await ctx.send("Please only use emojis in emoji field", ephemeral=True)
            return
        message = await ctx.fetch_message(message_id)
        if message is None:
            await ctx.send("Error, the roles message doesn't exist", ephemeral=True)
        success = await reactions.remove_emoji(message, emoji)
        if not success:
            # the emoji is already present
            await ctx.send("That emoji is not being used", ephemeral=True)
        else:
            await ctx.send("Deleted role reaction", ephemeral=True)
        
    @config.command(name="set_admin", description="sets a user as admin or not for chatparty", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def add_houseparty_admin(self, ctx, member: discord.Member, enable: bool):
        admin_role = discord.utils.get(ctx.guild.roles, name=DRole.ADMIN_ROLE.value)
        if enable:
            await member.add_roles(admin_role)
            msg = f'Added member ${member.name} to admin'
        else:
            await member.remove_roles(admin_role)
            msg = f'Removed member ${member.name} to admin'
        await ctx.send(msg)
        
    @config.command(name="set_broadcast_role", description="Sets the role to use for broadcasting for chatparty broadcasts", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def set_broadcast_role(self, ctx, role: Union[discord.Role, None], channel: Union[discord.VoiceChannel, None]):
        channel_id = -1
        if channel is not None:
            channel_id = channel.id
        if role is None:
            db.delete_guild_broadcast_role(ctx.guild.id, channel_id)
            if channel_id == -1:
                await ctx.send("Removed general broadcast role for this guild", ephemeral=True)
            else:
                await ctx.send("Removed broadcast role for channel " + channel.name, ephemeral=True)
        else:
            db.insert_guild_broadcast_role(role.guild.id, role.id)
            await ctx.send("Added broadcast role for this guild", ephemeral=True)
        
    @refresh.command(name="clear", description="clear all chat party related channels", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def clear_command(self, ctx):
        guild = ctx.guild
        # will be global command for configuring but for now just reset guild
        
        broadcasts = discord.utils.get(guild.categories, name=f'broadcast')
        sneak_chat = discord.utils.get(guild.categories, name=f'sneak')
        notifications_chat = discord.utils.get(guild.categories, name=f'notifications')
        private_channels = discord.utils.get(guild.categories, name=f'private_house_channel')
        delete_sub_channels_and_category(guild, [broadcasts, sneak_chat, notifications_chat, private_channels])
        
        await ctx.send('Finished Deleting channels')
        
    @refresh.command(name="create", description="create all house party related channels", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def create_command(self, ctx):
        guild = ctx.guild
        await setup_guild(guild, self.bot)
        await ctx.send('Finished creating channels, roles, and categories')
    
    @commands.guild_only()
    @chatparty.command(name="private", description="Command to lock your channel with the people inside", with_app_command=True)
    async def private(self, ctx: commands.Context):
        guild = ctx.guild
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
        house_party_role = get_bot_role(self.bot, ctx.guild)
        if house_party_role is None:
            print("error no bot default role")
        category = discord.utils.get(guild.categories, name=f'private_house_channel')
        perms = {'speak': True, 'view_channel': True, 'connect': True, 'use_voice_activation': True, }
        overwrite = discord.PermissionOverwrite(**perms)
        bot_account = discord.PermissionOverwrite(**{'speak': False, 'view_channel': True, 'connect': True})
        new_channel = await guild.create_voice_channel(name=f'{member.name}-PrivateRole', category=category, overwrites={role: overwrite, house_party_role: bot_account})
        
        # set the private_house_party_role so we can delete this later
        private_house_role = discord.utils.get(guild.roles, name=DRole.PRIVATE_ROLE.value)
        overwrite = discord.PermissionOverwrite()
        await new_channel.set_permissions(private_house_role, reason='Temp role for deleting channel when done', overwrite=overwrite)
        
        # iterate through channel members and set role then move
        tasks = []
        for member in c.members:
            await member.add_roles(role)
            await member.move_to(new_channel)
            # tasks.append(member.add_roles(role))
            #tasks.append(member.move_to(new_channel))
        await asyncio.gather(*tasks)
        await ctx.send('Locking channel')
        
    @commands.guild_only()
    @chatparty.command(name="quiz", description="Quiz command", with_app_command=True)
    async def quiz(self, ctx: commands.Context, action: Literal['start']):
        message = await ctx.send('starting quiz')
        await quiz.track_quiz(message)
        
    @create_command.error
    @clear_command.error
    @add_houseparty_admin.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('Only the owner of this bot can run this command')
        elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole) or isinstance(error, commands.CheckFailure):
            await ctx.send('You have to be an admin or have the role houseparty-admin')
        else:
            print(error)
            