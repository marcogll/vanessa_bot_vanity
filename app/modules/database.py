import logging

# MOCK DATABASE MODULE
# Since the actual DB is removed temporarily, this module provides mock implementations.

SessionUsersAlma = None
SessionVanityHr = None
SessionVanityAttendance = None

_REGISTERED_USERS = set()

def chat_id_exists(chat_id: int) -> bool:
    """Mock check: returns True if user is in in-memory set."""
    return False

def register_user(user_data: dict) -> bool:
    """Mock register: adds user to in-memory set."""
    # This function is now a no-op to ensure statelessness.
    # It always returns True to not break the conversation flow.
    return True
