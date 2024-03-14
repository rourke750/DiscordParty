from . import *
from . import __all__
from importlib import import_module

def enable_events():
    for module in __all__:
        dynamically_loaded_module = import_module(f'.{module}', 'discordparty.events')
        dynamically_loaded_module.enable_events()
    
def set_bot(bot):
    for module in __all__:
        dynamically_loaded_module = import_module(f'.{module}', 'discordparty.events')
        dynamically_loaded_module.set_bot(bot)
    
def add_random_fun_user(user_id, guild_id):
    random_events.add_user(user_id, guild_id)