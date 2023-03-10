from enum import Enum

class DRole(Enum):
    PRIVATE_ROLE = 'private_house_party_role'
    ADMIN_ROLE = 'houseparty_admin'
    BROADCAST_ROLE = 'chat_party_broadcast' # used for broadcast without deleting channel
    BROADCAST_DELETE_ROLE = 'chat_party_delete_broadcast' # used for broadcast with delete channel if empty