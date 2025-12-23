import logging

# MOCK DATABASE MODULE
# Since the actual DB is removed temporarily, this module provides mock implementations.

SessionUsersAlma = None
SessionVanityHr = None
SessionVanityAttendance = None

_REGISTERED_USERS = set()

def chat_id_exists(chat_id: int) -> bool:
    """Mock check: returns True if user is in in-memory set."""
    return int(chat_id) in _REGISTERED_USERS

def register_user(user_data: dict) -> bool:
    """Mock register: adds user to in-memory set."""
    try:
        meta = user_data.get("meta", {})
        metadata = user_data.get("metadata", {})
        tid = meta.get("telegram_id") or metadata.get("telegram_id") or metadata.get("chat_id")

        if tid:
            _REGISTERED_USERS.add(int(tid))
            logging.info(f"[MockDB] User {tid} registered in memory.")
            return True
        logging.warning("[MockDB] Could not find telegram_id in user_data.")
        return False
    except Exception as e:
        logging.error(f"[MockDB] Register error: {e}")
        return False


def deregister_user(chat_id: int) -> bool:
    """Mock deregister: removes user from in-memory set."""
    try:
        _REGISTERED_USERS.discard(int(chat_id))
        logging.info(f"[MockDB] User {chat_id} deregistered from memory.")
        return True
    except Exception as e:
        logging.error(f"[MockDB] Deregister error: {e}")
        return False
