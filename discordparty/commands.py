from discord.ext import commands
from discord.ext.commands import has_permissions, has_role

from .utils.utils import *
from .utils.checks import *
from .db import db

import datetime

from typing import Literal

import asyncio

class DiscordPartyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx, all=False):
        print('sync command')
        if not all:
            self.bot.tree.clear_commands(guild=ctx.guild)
            self.bot.tree.copy_global_to(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
        else:
            for guild in self.bot.guilds:
                self.bot.tree.clear_commands(guild=guild)
                await self.bot.tree.sync(guild=guild)
            await self.bot.tree.sync()
            
    @commands.guild_only()
    @commands.hybrid_group(name="houseparty", description="admin command", with_app_command=True)
    async def houseparty(self, ctx):
        await ctx.send("Parent command!")
        
    @commands.guild_only()
    @houseparty.command(name="time", description="Command to get all time this week", with_app_command=True)
    async def time(self, ctx: commands.Context, current=False):
        user_id = ctx.author.id
        end = int(datetime.datetime.timestamp(datetime.datetime.now()))
        current_week = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sub = current_week - datetime.timedelta(days=datetime.datetime.now().weekday(), hours=0, minutes=0, seconds=0)
        start = int(datetime.datetime.timestamp(sub))
        total_time = db.get_total_active_time_minutes(user_id, start, end)
        if not current:
            print(sub)
            total_time = total_time + db.get_arcival_time_minutes(user_id, sub)
            await ctx.send('Time since Monday %d minutes' % total_time)
        else:
            await ctx.send('Current time in voice %d minutes' % total_time)
        
    @commands.guild_only()
    @houseparty.group(name="admin", description="admin command", with_app_command=True)
    @commands.check(has_permission_or_role)
    async def admin(self, ctx):
        await ctx.send("Parent command!")
        
    @commands.guild_only()
    @admin.command(name="broadcast", description="Set channel to allow broadcasts from", with_app_command=True)
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
    @houseparty.group(name="refresh", description="allow refreshing of channels", with_app_command=True)
    @commands.check(has_permission_or_role)
    async def refresh(self, ctx):
        await ctx.send("Parent command!")
        
    @commands.guild_only()
    @houseparty.group(name="config", description="allow modifying house party configuration", with_app_command=True)
    @commands.check(has_permission_or_role)
    async def config(self, ctx):
        await ctx.send("Parent command!")
        
    @config.command(name="set_admin", description="sets a user as admin or not for houseparty", with_app_command=True)
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
            
        
    @refresh.command(name="clear", description="clear all house party related channels", with_app_command=True)
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
    @houseparty.command(name="private", description="Command to lock your channel with the people inside", with_app_command=True)
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
        house_party_roles = ctx.guild.get_member(self.bot.user.id).roles
        for bot_role in house_party_roles:
            if bot_role.is_bot_managed():
                house_party_role = bot_role
        if house_party_role is None:
            print("error no bot default role")
        #house_party_role = discord.utils.get(guild.roles, name=f'ChatParty')
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
            await member.add_roles(role)
            await member.move_to(new_channel)
            # tasks.append(member.add_roles(role))
            #tasks.append(member.move_to(new_channel))
        await asyncio.gather(*tasks)
        
        await ctx.send('Locking channel')
        
    @create_command.error
    @clear_command.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('Only the owner of this bot can run this command')
        elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole) or isinstance(error, commands.CheckFailure):
            await ctx.send('You have to be an admin or have the role houseparty-admin')
        else:
            print(error)
            