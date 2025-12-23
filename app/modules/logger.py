import logging
from modules.database import SessionUsersAlma

def log_request(telegram_id, username, command, message):
    if not SessionUsersAlma:
        # DB not configured, just log to console/file
        logging.info(f"REQ: {command} from {username} ({telegram_id}): {message}")
        return

    # DB logic removed as models are not available
    logging.info(f"REQ: {command} from {username} ({telegram_id}): {message}")

