from . import notifications, db_events, random_events

def enable_events():
    notifications.enable_events()
    db_events.enable_events()
    random_events.enable_events()
    
def set_bot(bot):
    notifications.set_bot(bot)
    db_events.set_bot(bot)
    random_events.set_bot(bot)
    
def add_random_fun_user(user_id, guild_id):
    random_events.add_user(user_id, guild_id)