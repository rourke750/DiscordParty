from . import notifications, db_events

def enable_events():
    notifications.enable_events()
    db_events.enable_events()
    
def set_bot(bot):
    notifications.set_bot(bot)
    db_events.set_bot(bot)