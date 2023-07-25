from __future__ import with_statement
from contextlib import closing

from . import db

import datetime

TABLE_VERSION = 1

SELECT_VERSION = 'SELECT MAX(version) as max_ver FROM versions;'
INSERT_VERSION = '''INSERT INTO versions ('version', 'timestamp') VALUES (?, ?)'''

def insert_version(cur, version):
    values = (version, int(datetime.datetime.timestamp(datetime.datetime.now())))
    cur.execute(INSERT_VERSION, values)

def should_perform_upgrade(cur):
    cur.execute(SELECT_VERSION)
    row = cur.fetchone()
    
    if row[0] is None:
        # there have been no upgrades, just set it to table version
        insert_version(cur, TABLE_VERSION)
        
def upgrade():
    # first check if we need to upgrade
    with closing(db.con.cursor()) as cur:
        should_perform_upgrade(cur)
        db.con.commit()