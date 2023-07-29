import discord

import asyncio

class SupressWave(discord.ui.View):
    @discord.ui.button(label='mute', style=discord.ButtonStyle.red)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('You will not recieve these notifications', ephemeral=True)
        
    @discord.ui.button(label='mute 1 hr', style=discord.ButtonStyle.red)
    async def mute_1_hr(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('You will not recieve these notifications for 1 hour', ephemeral=True)
        
class QuizView(discord.ui.View):
    DELAYED_TIME = 10
    
    def __init__(self):
        super().__init__()
        self.clear()
        self.message = None
        
        self.current_question_count = 0
        self.max_questions = 5
        
        # keep track of points
        self.points = {}
        
    async def quiz_ended(self, delay):
        self.current_question_count = self.current_question_count + 1
        await asyncio.sleep(delay)
        total = self.total()
        # go through the labels and set colors and percents based on what was selected and correct answer
        for c in self.children:
            if c.label != self.correct_answer_letter:
                c.style = discord.ButtonStyle.red
            count = '0'
            if self.m[c.label] > 0:
                count = str(int(self.m[c.label] / total * 100))
            c.label = f'{c.label} {count}%'
            c.disabled = True
            
        # now update the points
        for id in self.response:
            # check if user is in points mapping
            if id not in self.points:
                self.points[id] = 0
            answer = self.response[id]
            if answer == self.correct_answer_letter:
                self.points[id] = self.points[id] + 1
            
        # update labels with percents
        await self.message.edit(view=self)
        # now just block for a little bit to keep results up
        await asyncio.sleep(5)
    
    def is_quiz_ended(self):
        return self.current_question_count >= self.max_questions
        
    async def send_results(self):
        update_message = self.get_points_by_username()
        await self.message.edit(content=update_message, view=None)
        
    def get_points_by_username(self):
        response = 'Quiz over'
        for id in self.points:
            response = response + '\n'
            user = self.message.guild.get_member(id)
            display_name = user.display_name
            points = self.points[id]
            response = response + f'{display_name} has {points} points'
        return response
       
    def total(self):
        count = 0
        for k in self.m:
            count = count + self.m[k]
        return count
        
    def clear(self, reset=False):
        self.m = {'a':0, 'b':0, 'c':0, 'd':0}
        self.response = {}
        self.correct_answer_letter = None
        if reset:
            for c in self.children:
                c.style = discord.ButtonStyle.green
                c.label = c.label[0]
                c.disabled = False
        
    # return an awaitable
    def claim_position(self, interaction, letter):
        id = interaction.user.id
        if id in self.response:
            # user already picked an answer
            return interaction.response.send_message(f'You have already selected position {self.response[id]}', ephemeral=True)
        else:
            self.response[id] = letter
            self.m[letter] = self.m[letter] + 1
        return interaction.response.defer()
        
    @discord.ui.button(label='a', style=discord.ButtonStyle.green)
    async def a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_position(interaction, 'a')
    @discord.ui.button(label='b', style=discord.ButtonStyle.green)
    async def b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_position(interaction, 'b')
    @discord.ui.button(label='c', style=discord.ButtonStyle.green)
    async def c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_position(interaction, 'c')
    @discord.ui.button(label='d', style=discord.ButtonStyle.green)
    async def d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.claim_position(interaction, 'd')