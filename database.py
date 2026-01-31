# database.py
import logging

logger = logging.getLogger(__name__)

# Data RAM mein save hoga
temp_stats = {'total_messages': 0, 'total_users': 0, 'total_groups': 0}
temp_chats = set()

def init_db():
    logger.info("RAM storage initialized.")

def update_chat_info(chat_id, chat_type, is_new=False):
    temp_stats['total_messages'] += 1
    if chat_id not in temp_chats:
        temp_chats.add(chat_id)
        if chat_type == 'private': temp_stats['total_users'] += 1
        else: temp_stats['total_groups'] += 1

def get_stats(): return temp_stats
def get_all_chat_ids(): return list(temp_chats)
