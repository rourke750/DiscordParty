from ..db import db

import emoji as emoji_i
import asyncio

import logging

# we will store messages we are watching in mem but dont need to worry about roles since that wont occur often
MESSAGE_LOOKUP = {}

def get_generic_params(payload, bot=None):
    message_id = payload.message_id
    emoji_id = emoji_i.demojize(payload.emoji.name)
    member = None
    if bot is not None:
        member = bot.get_guild(payload.guild_id).get_member(payload.user_id)
    else:
        member = payload.member
    # get the role for the emoji_id
    role_id = db.get_role_from_guild_reaction(message_id, emoji_id)
    if role_id is None:
        logging.error('There was an issue getting the guild reaction returned role was none')
        return None, None
    role = member.guild.get_role(role_id)
    if role is None:
        logging.error('The role was none from guild')
        return None, None
    return role, member

async def on_raw_reaction_add(payload):
    message_id = payload.message_id
    # check if message_id is in map
    if message_id not in MESSAGE_LOOKUP:
        return
    role, member = get_generic_params(payload)
    if role is not None:
        await member.add_roles(role, reason='Added role to user from roles message')
    
async def on_raw_reaction_remove(bot, payload):
    message_id = payload.message_id
    # check if message_id is in map
    if message_id not in MESSAGE_LOOKUP:
        return
    role, member = get_generic_params(payload, bot)
    if role is not None:
        await member.remove_roles(role, reason='Removed role to user from roles message')
        
async def add_emoji_with_description(message, emoji, description, role):
    message.content = message.content + f'\n{emoji}: {description}'
    for r in message.reactions:
        if r.emoji == emoji:
            return False
    # now add to db
    db.insert_role_for_reaction_id(message.id, role.id, emoji_i.demojize(emoji))
    # add to message
    l = []
    l.append(message.add_reaction(emoji))
    l.append(message.edit(content=message.content))
    await asyncio.gather(*l)
    return True
    
async def remove_emoji(message, emoji):
    found = False
    for r in message.reactions:
        if r.emoji == emoji:
            found = True
            break
    if not found:
        return False
        
    # now go through and remove emoji and description
    new_edit = ''
    for m in message.content.split('\n'):
        if not m.startswith(emoji):
            if new_edit != '':
                new_edit = new_edit + '\n'
            new_edit = new_edit + m
    
    l = []
    l.append(message.clear_reaction(emoji))
    l.append(message.edit(content=new_edit))
    await asyncio.gather(*l)
    return True
    
def track_new_message_id(message_id, guild_id):
    MESSAGE_LOOKUP[message_id] = True
    db.insert_message_id_for_guild(message_id, guild_id)
    
def untrack_message_id(message_id):
    MESSAGE_LOOKUP.pop('key', None)
    db.delete_message_id_for_guild(message_id)
    
message_ids = db.get_all_message_ids()

# now change array into map for faster indexing
for id in message_ids:
    MESSAGE_LOOKUP[id] = True