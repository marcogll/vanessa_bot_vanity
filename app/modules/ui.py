from telegram import ReplyKeyboardMarkup


def main_actions_keyboard(is_registered: bool = False) -> ReplyKeyboardMarkup:
    """Teclado inferior con comandos directos (un toque lanza el flujo)."""
    keyboard = []
    if not is_registered:
        keyboard.append(["/registro"])
    
    keyboard.extend([
        ["/vacaciones", "/permiso"],
        ["/links", "/start"],
    ])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )
