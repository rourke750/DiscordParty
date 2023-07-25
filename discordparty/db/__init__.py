from . import db, upgrades

db.create_tables()
db.create_triggers()
upgrades.upgrade()