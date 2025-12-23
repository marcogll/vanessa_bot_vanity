import os
import logging
from dotenv import load_dotenv
from typing import Optional

# Cargar variables de entorno antes de importar módulos que las usan
load_dotenv()

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, CommandHandler, ContextTypes

# --- IMPORTAR HABILIDADES ---
from modules.flow_builder import load_flows
from modules.logger import log_request
from modules.database import chat_id_exists  # Importar chat_id_exists
from modules.ui import main_actions_keyboard

from modules.rh_requests import vacaciones_handler, permiso_handler
# from modules.finder import finder_handler (Si lo creas después)

# Cargar links desde variables de entorno
LINK_CURSOS = os.getenv(
    "LINK_CURSOS", "https://cursos.vanityexperience.mx/dashboard-2/"
)
LINK_SITIO = os.getenv("LINK_SITIO", "https://vanityexperience.mx/")
LINK_AGENDA_IOS = os.getenv(
    "LINK_AGENDA_IOS", "https://apps.apple.com/us/app/fresha-for-business/id1455346253"
)
LINK_AGENDA_ANDROID = os.getenv(
    "LINK_AGENDA_ANDROID",
    "https://play.google.com/store/apps/details?id=com.fresha.Business",
)


TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def _guess_platform(update: Update) -> Optional[str]:
    """
    Telegram no expone el OS del usuario en mensajes regulares.
    Devolvemos None para mostrar ambos links; si en el futuro llegan datos, se pueden mapear aquí.
    """
    try:
        _ = update.to_dict()  # placeholder por si queremos inspeccionar el payload
    except Exception:
        pass
    return None


async def links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra accesos rápidos a cursos, sitio y descargas."""
    user = update.effective_user
    log_request(user.id, user.username, "links", update.message.text)

    plataforma = _guess_platform(update)
    descarga_buttons = []
    if plataforma == "ios":
        descarga_buttons.append(
            InlineKeyboardButton("Agenda | iOS", url=LINK_AGENDA_IOS)
        )
    elif plataforma == "android":
        descarga_buttons.append(
            InlineKeyboardButton("Agenda | Android", url=LINK_AGENDA_ANDROID)
        )
    else:
        descarga_buttons = [
            InlineKeyboardButton("Agenda | iOS", url=LINK_AGENDA_IOS),
            InlineKeyboardButton("Agenda | Android", url=LINK_AGENDA_ANDROID),
        ]

    texto = (
        "🌐 Links útiles\n"
        "Claro, aquí tienes enlaces que puedes necesitar durante tu estancia con nosotros:\n"
        "Toca el que te aplique."
    )
    botones = [
        [InlineKeyboardButton("Cursos Vanity", url=LINK_CURSOS)],
        [InlineKeyboardButton("Sitio Vanity", url=LINK_SITIO)],
        descarga_buttons,
    ]
    await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(botones))


async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de opciones de Vanessa"""
    user = update.effective_user
    log_request(user.id, user.username, "start", update.message.text)
    texto = (
        "👩‍💼 **Hola, soy Vanessa. ¿En qué puedo ayudarte hoy?**\n\n"
        "Toca un botón para continuar 👇"
    )
    is_registered = chat_id_exists(user.id)
    await update.message.reply_text(
        texto, reply_markup=main_actions_keyboard(is_registered=is_registered)
    )


async def post_init(application: Application):
    # Mantén los comandos rápidos disponibles en el menú de Telegram
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Mostrar menú principal"),
            # BotCommand("welcome", "Registro de nuevas empleadas"), # Se maneja dinámicamente
            BotCommand("horario", "Definir horario de trabajo"),
            BotCommand("vacaciones", "Solicitar vacaciones"),
            BotCommand("permiso", "Solicitar permiso por horas"),
            BotCommand("links", "Links útiles"),
            BotCommand("cancelar", "Cancelar operación actual"),
        ]
    )

    # Cargar flujos dinámicos
    handlers = load_flows()
    for handler in handlers:
        application.add_handler(handler)

    logging.info("🤖 Vanessa Bot iniciado y listo.")


def main():
    """Punto de entrada"""
    if not TOKEN:
        logging.error("❌ No se encontró TELEGRAM_TOKEN en variables de entorno.")
        return

    defaults = Defaults(parse_mode=ParseMode.MARKDOWN)
    app = (
        Application.builder()
        .token(TOKEN)
        .defaults(defaults)
        .post_init(post_init)
        .build()
    )

    # Handlers globales
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CommandHandler("help", menu_principal))
    app.add_handler(CommandHandler("links", links_menu))

    # Handlers de módulos
    app.add_handler(vacaciones_handler)
    app.add_handler(permiso_handler)

    # El flow_builder carga el resto desde conv-flows/

    logging.info("Iniciando polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
