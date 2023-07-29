import discord

class SupressWave(discord.ui.View):
    @discord.ui.button(label='mute', style=discord.ButtonStyle.red)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('You will not recieve these notifications', ephemeral=True)
        
    @discord.ui.button(label='mute 1 hr', style=discord.ButtonStyle.red)
    async def mute_1_hr(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('You will not recieve these notifications for 1 hour', ephemeral=True)