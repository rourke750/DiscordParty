from __future__ import with_statement
from contextlib import closing

import sqlite3
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

PATH = os.getenv("DISCORD_DB_PATH")

con = sqlite3.connect(os.path.join(PATH, 'discord_party.db'))

CREATE_TIME_TABLE = 'CREATE TABLE IF NOT EXISTS time_record (discord_id INT, start INT, end INT);'

INSERT_TIME_FOR_ID = '''INSERT INTO time_record ('discord_id', 'start') VALUES (?, ?);'''
UPDATE_TIME_FOR_ID = '''UPDATE time_record SET end = ? where end IS NULL AND discord_id = ?;'''
GET_TIME_FOR_ID = '''SELECT start, end FROM time_record WHERE discord_id = ? and start >= ? and start <= ?;'''

def insert_time(discord_id, start):
    print('inserting time for %s %d' % (discord_id, start))
    with closing(con.cursor()) as cur:
        values = (discord_id, int(start))
        cur.execute(INSERT_TIME_FOR_ID, values)
        con.commit()
        
def update_end_time(discord_id, end):
    print('updating time for %s %d' % (discord_id, end))
    with closing(con.cursor()) as cur:
        values = (int(end), discord_id)
        cur.execute(UPDATE_TIME_FOR_ID, values)
        con.commit()
        
def get_total_time_minutes(discord_id, start, end):
    with closing(con.cursor()) as cur:
        values = (discord_id, int(start), int(end))
        cur.execute(GET_TIME_FOR_ID, values)
        rows = cur.fetchall()
        t = 0
        for row in rows:
            if row[1] is not None:
                t += row[1]-row[0]
            else:
                t += int(datetime.datetime.timestamp(datetime.datetime.now())) - row[0]
        t = int(t / 60) # convert to minutes
        return t

def create_tables():
    with closing(con.cursor()) as cur:
        print('creating tables')
        cur.execute(CREATE_TIME_TABLE)
        print('created tables')
    
def create_indexes():
    pass
