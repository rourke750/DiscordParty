from __future__ import with_statement
from contextlib import closing

import sqlite3
import os
from dotenv import load_dotenv
import datetime
import logging

load_dotenv()

PATH = os.getenv("DISCORD_DB_PATH")

con = sqlite3.connect(os.path.join(PATH, 'discord_party.db'))

CREATE_TIME_TABLE = 'CREATE TABLE IF NOT EXISTS time_record (discord_id INT, start INT, end INT);'
CREATE_VERSION_TABLE = 'CREATE TABLE IF NOT EXISTS versions (version INT, timestamp INT);'
CREATE_TIME_ARCIVAL_TABLE = 'CREATE TABLE IF NOT EXISTS time_record_arcival (discord_id INT, week_num INT, total_time INT, PRIMARY KEY(discord_id, week_num));'
CREATE_MUTE_TABLE = 'CREATE TABLE IF NOT EXISTS mute_record (discord_id INT, expiry INT, PRIMARY KEY(discord_id));'
CREATE_GUILD_ROLE_TABLE = 'CREATE TABLE IF NOT EXISTS guild_role_table (guild_id INT, role_id INT, channel_id INT, PRIMARY KEY (guild_id, channel_id));'
CREATE_REACTION_MESSAGE_TABLE = 'CREATE TABLE IF NOT EXISTS guild_message_id_table (message_id INT, guild_id INT, PRIMARY KEY(guild_id, message_id));'
CREATE_MESSAGE_TO_REACTION_TABLE = 'CREATE TABLE IF NOT EXISTS guild_reaction_to_role_table(message_id INT, role_id INT, reaction_id text);'

# create trigger for moving data from one time_record to consolidated
CREATE_TRIGGER_TIME_MOVEMENT = '''
            CREATE TRIGGER update_time_record_arcival UPDATE OF end ON time_record 
              BEGIN
                INSERT INTO time_record_arcival (discord_id, week_num, total_time) 
                VALUES (old.discord_id, datetime(new.start, 'unixepoch', 'weekday 1', '-7 day', 'start of day'), (SELECT IFNULL(sum(end - start), 0) as s FROM time_record WHERE discord_id = old.discord_id AND end IS NOT NULL) + new.end - new.start)
                on CONFLICT(discord_id, week_num) DO UPDATE SET
                    total_time = total_time + excluded.total_time
                    WHERE discord_id = excluded.discord_id AND week_num = excluded.week_num;
                DELETE FROM time_record WHERE discord_id = old.discord_id;
              END;
'''

INSERT_TIME_FOR_ID = '''INSERT INTO time_record ('discord_id', 'start') VALUES (?, ?);'''
UPDATE_TIME_FOR_ID = '''UPDATE time_record SET end = ? where end IS NULL AND discord_id = ?;'''

GET_ACTIVE_TIME_FOR_ID = '''SELECT start, end FROM time_record WHERE discord_id = ? and start >= ? and start <= ?;'''
GET_ACTIVE_TIME = '''SELECT discord_id, start, end FROM time_record;'''
GET_ARCIVED_TIME = '''SELECT IFNULL(total_time, 0) FROM time_record_arcival WHERE discord_id = ? AND week_num = ?;'''

INSERT_USER_MUTED = '''INSERT INTO mute_record('discord_id', 'expiry') VALUES (?, ?);'''
UPDATE_USER_MUTED = '''UPDATE mute_record SET expiry = ? WHERE discord_id = ?;'''
DELETE_USER_MUTED = '''DELETE FROM mute_record WHERE discord_id = ?;'''
IS_USER_MUTED = '''SELECT expiry FROM mute_record WHERE discord_id = ?;''';
GET_ALL_EXPIRED_MUTES = '''SELECT discord_id FROM mute_record WHERE expiry != -1 AND expiry < ?;'''

INSERT_GUILD_BROADCAST_ROLE = '''INSERT OR REPLACE INTO guild_role_table (guild_id, role_id, channel_id) VALUES(?, ?, ?);'''
GET_GUILD_BROADCAST_ROLE = '''SELECT role_id, channel_id FROM guild_role_table WHERE guild_id = ? AND (channel_id = ? OR channel_id = -1);'''
DELETE_GUILD_BROADCAST_ROLE = '''DELETE FROM guild_role_table WHERE guild_id = ? AND channel_id = ?;'''

SELECT_ALL_MESSAGE_IDS = '''SELECT message_id FROM guild_message_id_table;'''
INSERT_MESSAGE_ID_FOR_GUILD = '''INSERT INTO guild_message_id_table (message_id, guild_id) VALUES(?, ?);'''
DELETE_MESSAGE_ID_FOR_GUILD = '''DELETE FROM guild_message_id_table WHERE message_id = ?;'''
DELETE_MESSAGE_ID_FOR_GUILD_REACTION = '''DELETE FROM guild_reaction_to_role_table WHERE message_id = ?;'''
SELECT_MESSAGE_ID_FOR_GUILD = '''SELECT message_id FROM guild_message_id_table WHERE guild_id = ?;'''
INSERT_EMOJI_TO_ROLE_FOR_GUILD_REACTION = '''INSERT INTO guild_reaction_to_role_table (message_id, role_id, reaction_id) values (?, ?, ?);'''
SELECT_ROLE_FROM_EMOJI = '''SELECT role_id FROM guild_reaction_to_role_table WHERE message_id = ? AND reaction_id = ?;'''

def get_role_from_guild_reaction(message_id, reaction_id):
    with closing(con.cursor()) as cur:
        values = (message_id, reaction_id)
        cur.execute(SELECT_ROLE_FROM_EMOJI, values)
        rows = cur.fetchone()
        if rows is None or len(rows) == 0:
            return None
        return rows[0]

def insert_role_for_reaction_id(message_id, role_id, reaction_id):
    with closing(con.cursor()) as cur:
        values = (message_id, role_id, reaction_id)
        cur.execute(INSERT_EMOJI_TO_ROLE_FOR_GUILD_REACTION, values)
        con.commit()

def get_message_id_for_guild(guild_id):
    with closing(con.cursor()) as cur:
        values = (guild_id,)
        cur.execute(SELECT_MESSAGE_ID_FOR_GUILD, values)
        rows = cur.fetchone()
        if rows is None or len(rows) == 0:
            return None
        return rows[0]

def delete_message_id_for_guild(message_id):
    with closing(con.cursor()) as cur:
        values = (message_id,)
        cur.execute(DELETE_MESSAGE_ID_FOR_GUILD, values)
        cur.execute(DELETE_MESSAGE_ID_FOR_GUILD_REACTION, values)
        con.commit()

def insert_message_id_for_guild(message_id, guild_id):
    with closing(con.cursor()) as cur:
        values = (message_id, guild_id)
        cur.execute(INSERT_MESSAGE_ID_FOR_GUILD, values)
        con.commit()

def get_all_message_ids():
    with closing(con.cursor()) as cur:
        cur.execute(SELECT_ALL_MESSAGE_IDS)
        rows = cur.fetchall()
        if rows is None or len(rows) == 0:
            return []
        return [x[0] for x in rows]

def insert_guild_broadcast_role(guild_id, role_id, channel_id=-1):
    with closing(con.cursor()) as cur:
        values = (guild_id, role_id, channel_id)
        cur.execute(INSERT_GUILD_BROADCAST_ROLE, values)
        con.commit()
        
def delete_guild_broadcast_role(guild_id, channel_id=-1):
    with closing(con.cursor()) as cur:
        values = (guild_id, channel_id)
        cur.execute(DELETE_GUILD_BROADCAST_ROLE, values)
        con.commit()

def get_guild_broadcast_role(guild_id, channel_id=-1):
    with closing(con.cursor()) as cur:
        values = (guild_id, channel_id)
        cur.execute(GET_GUILD_BROADCAST_ROLE, values)
        rows = cur.fetchall()
        if len(rows) == 0:
            return None
        # we can have two one thats general and one thats channel specific, if two return the one that isnt -1
        if len(rows) == 2:
            for row in rows:
                if row[1] != -1:
                    return row[0]
        return rows[0][0]

def insert_time(discord_id, start):
    logging.debug('inserting time for %s %d' % (discord_id, start))
    with closing(con.cursor()) as cur:
        values = (discord_id, int(start))
        cur.execute(INSERT_TIME_FOR_ID, values)
        con.commit()
        
def insert_user_muted(discord_id, expiry):
    with closing(con.cursor()) as cur:
        values = (discord_id, int(expiry))
        cur.execute(INSERT_USER_MUTED, values)
        con.commit()
        
def update_user_muted(discord_id, expiry):
    with closing(con.cursor()) as cur:
        values = (int(expiry), discord_id)
        cur.execute(UPDATE_USER_MUTED, values)
        con.commit()
        
def delete_user_muted(discord_id):
    with closing(con.cursor()) as cur:
        values = (discord_id,)
        cur.execute(DELETE_USER_MUTED, values)
        con.commit()
        
def delete_users_muted(discord_ids):
    with closing(con.cursor()) as cur:
        values = [(discord_id,) for discord_id in discord_ids]
        cur.executemany(DELETE_USER_MUTED, values)
        con.commit()
        
def get_user_muted(discord_id):
    with closing(con.cursor()) as cur:
        values = (discord_id,)
        cur.execute(IS_USER_MUTED, values)
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]
        
def get_all_user_muted_expired(t):
    with closing(con.cursor()) as cur:
        values = (t,)
        cur.execute(GET_ALL_EXPIRED_MUTES, values)
        rows = cur.fetchall()
        if rows is None:
            return None
        return [x[0] for x in rows]
        
def update_end_time(discord_id, end):
    logging.debug('updating time for %s %d' % (discord_id, end))
    with closing(con.cursor()) as cur:
        values = (int(end), discord_id)
        cur.execute(UPDATE_TIME_FOR_ID, values)
        con.commit()
        
def get_total_active_time_minutes(discord_id, start, end):
    with closing(con.cursor()) as cur:
        values = (discord_id, int(start), int(end))
        cur.execute(GET_ACTIVE_TIME_FOR_ID, values)
        rows = cur.fetchall()
        t = 0
        for row in rows:
            if row[1] is not None:
                t += row[1]-row[0]
            else:
                t += int(datetime.datetime.timestamp(datetime.datetime.now())) - row[0]
        t = int(t / 60) # convert to minutes
        return t
        
def get_arcival_time_minutes(discord_id, week):
    with closing(con.cursor()) as cur:
        values = (discord_id, week)
        cur.execute(GET_ARCIVED_TIME, values)
        rows = cur.fetchone()
        if rows is None:
            return 0
        return int(rows[0] / 60)
        
# returns a map of current session from discord_id to seconds
def get_current_session_time():
    with closing(con.cursor()) as cur:
        cur.execute(GET_ACTIVE_TIME)
        rows = cur.fetchall()
        t = {}
        for row in rows:
            discord_id = row[0]
            start = row[1]
            end = row[2]
            if end is None:
                end = int(datetime.datetime.timestamp(datetime.datetime.now()))
            # check if discord id is present and if it is not add it to map
            if discord_id not in t:
                t[discord_id] = 0
            # now add time to existing
            t[discord_id] = t[discord_id] + end - start
        return t

def create_tables():
    with closing(con.cursor()) as cur:
        logging.debug('creating tables')
        cur.execute(CREATE_TIME_TABLE)
        cur.execute(CREATE_VERSION_TABLE)
        cur.execute(CREATE_TIME_ARCIVAL_TABLE)
        cur.execute(CREATE_MUTE_TABLE)
        cur.execute(CREATE_GUILD_ROLE_TABLE)
        cur.execute(CREATE_REACTION_MESSAGE_TABLE)
        cur.execute(CREATE_MESSAGE_TO_REACTION_TABLE)
        logging.debug('created tables')
        
def create_triggers():
    with closing(con.cursor()) as cur:
        cur.execute('DROP TRIGGER IF EXISTS update_time_record_arcival;')
        cur.execute(CREATE_TRIGGER_TIME_MOVEMENT)
        
def create_indexes():
    pass
