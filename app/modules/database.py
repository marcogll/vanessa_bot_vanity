import logging
import os

# --- CONFIGURACIÓN DE PERSISTENCIA ---
# Usamos un archivo de texto para persistir los chat_id de usuarios registrados.
# Esto es una solución temporal y ligera hasta que se implemente una base de datos.
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
USERS_FILE = os.path.join(DATA_DIR, "registered_users.txt")

# Asegurarse de que el directorio de datos exista
os.makedirs(DATA_DIR, exist_ok=True)


# MOCK DATABASE MODULE
# Since the actual DB is removed temporarily, this module provides mock implementations.

SessionUsersAlma = None
SessionVanityHr = None
SessionVanityAttendance = None

_REGISTERED_USERS = set()


def load_registered_users():
    """Carga los chat_id de usuarios registrados desde el archivo de texto."""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                for line in f:
                    try:
                        _REGISTERED_USERS.add(int(line.strip()))
                    except ValueError:
                        logging.warning(
                            f"[DB] Se ignoró una línea no válida en {USERS_FILE}: {line.strip()}"
                        )
            logging.info(
                f"[DB] Se cargaron {len(_REGISTERED_USERS)} usuarios registrados desde {USERS_FILE}"
            )
        else:
            logging.info(f"[DB] No se encontró el archivo de usuarios en {USERS_FILE}, se creará uno nuevo al primer registro.")
    except Exception as e:
        logging.error(f"[DB] Error al cargar usuarios registrados: {e}")


def chat_id_exists(chat_id: int) -> bool:
    """Mock check: returns True if user is in in-memory set."""
    return int(chat_id) in _REGISTERED_USERS


def register_user(user_data: dict) -> bool:
    """
    Mock register: adds user to in-memory set and appends to the persistence file.
    """
    try:
        meta = user_data.get("meta", {})
        metadata = user_data.get("metadata", {})
        tid = meta.get("telegram_id") or metadata.get("telegram_id") or metadata.get("chat_id")

        if tid:
            chat_id = int(tid)
            if chat_id not in _REGISTERED_USERS:
                _REGISTERED_USERS.add(chat_id)
                # Persistir en el archivo de texto
                with open(USERS_FILE, "a") as f:
                    f.write(f"{chat_id}\n")
                logging.info(f"[DB] User {chat_id} registered in memory and persisted to file.")
            else:
                logging.info(f"[DB] User {chat_id} was already registered.")
            return True

        logging.warning("[DB] Could not find telegram_id in user_data to register.")
        return False
    except (ValueError, TypeError) as e:
        logging.error(f"[DB] Invalid telegram_id format: {tid}. Error: {e}")
        return False
    except Exception as e:
        logging.error(f"[DB] Register error: {e}")
        return False
