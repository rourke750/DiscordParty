from discord.ext import commands
from discord.ext.commands import has_permissions, has_role

from .utils.utils import *
from .utils.checks import *

class DiscordPartyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx, all=False):
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
    @commands.hybrid_group(name="houseparty", description="admin command", with_app_command=True)
    async def houseparty(self, ctx):
        await ctx.send("Parent command!")
        
    @houseparty.command(name="clear", description="clear all house party related channels", with_app_command=True)
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
        
    @houseparty.command(name="create", description="create all house party related channels", with_app_command=True)
    @commands.guild_only()
    @commands.check(has_permission_or_role)
    async def create_command(self, ctx):
        guild = ctx.guild
        await setup_guild(guild)
        await ctx.send('Finished creating channels, roles, and categories')
        
    def delete_sub_channels_and_category(self, guild, categories):
        channels = []
        for cat in categories:
            for chan in cat.channels:
                channels.append(chan.delete())
            channels.append(cat.delete())
        asyncio.gather(*channels)
                

    @commands.guild_only()
    @houseparty.command(name="private", description="Command to lock your channel with the people inside", with_app_command=True)
    async def private(self, ctx: commands.Context):
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
    async def command_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send('Only the owner of this bot can run this command')
        elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole) or isinstance(error, commands.CheckFailure):
            await ctx.send('You have to be an admin or have the role houseparty-admin')
        else:
            print(error)
            