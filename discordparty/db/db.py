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

def insert_time(discord_id, start):
    logging.debug('inserting time for %s %d' % (discord_id, start))
    with closing(con.cursor()) as cur:
        values = (discord_id, int(start))
        cur.execute(INSERT_TIME_FOR_ID, values)
        con.commit()
        
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
        logging.debug('created tables')
        
def create_triggers():
    with closing(con.cursor()) as cur:
        cur.execute('DROP TRIGGER IF EXISTS update_time_record_arcival;')
        cur.execute(CREATE_TRIGGER_TIME_MOVEMENT)
        
def create_indexes():
    pass
