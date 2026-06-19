"""
Point d'entrée du LUST Downloader Bot.
Lance l'application Telegram (python-telegram-bot v20+) et enregistre
tous les handlers (commandes, callbacks, messages, erreurs).

Compatible Render / Railway / VPS : configuration via variables
d'environnement, fonctionnement en polling (aucun webhook requis).
"""

import logging
import sys

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN
from utils.storage import init_db
import handlers

# --------------------------------------------------------------------------
# Configuration des logs
# --------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("lust_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    """Construit et configure l'application Telegram."""
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN manquant. Définis la variable d'environnement BOT_TOKEN.")
        sys.exit(1)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(60)
        .write_timeout(60)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Commandes
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))

    # Boutons inline (menu, force-sub, choix de qualité...)
    application.add_handler(CallbackQueryHandler(handlers.callback_router))

    # Détection automatique des liens envoyés en texte libre
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message_handler)
    )

    # Gestion globale des erreurs -> anti-crash garanti
    application.add_error_handler(handlers.global_error_handler)

    return application


def main():
    init_db()
    application = build_application()
    logger.info("🚀 LUST Downloader Bot démarré (polling)...")
    application.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)


if __name__ == "__main__":
    main()
