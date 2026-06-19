"""
Configuration centrale du bot LUST Downloader Bot.
Toutes les valeurs sensibles sont chargées depuis les variables d'environnement.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Token du bot Telegram (obtenu via @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Lien utilisé par le bouton "📢 Communauté" du menu Développeur
DEV_COMMUNITY_LINK = os.getenv("DEV_COMMUNITY_LINK", "https://t.me/+oy1Jh6Xc5HFiZjE0")

# --------------------------------------------------------------------------
# CANAUX OBLIGATOIRES (Force Subscribe)
# --------------------------------------------------------------------------
# Pour un canal PUBLIC -> chat_id peut être le @username (ex: "@INFERNOxOTP")
# Pour un canal PRIVÉ (lien d'invitation type https://t.me/+xxxx), Telegram
# ne permet pas de retrouver automatiquement l'ID à partir du lien. Tu dois :
#   1. Ajouter le bot comme ADMINISTRATEUR du canal privé
#   2. Récupérer le chat_id réel (entier négatif, ex: -1001234567890)
#      -> envoie un message dans le canal, transfère-le à @JsonDumpBot,
#         ou utilise un bot utilitaire comme @username_to_id_bot
#   3. Renseigne CHANNEL_1_ID et CHANNEL_3_ID dans le fichier .env
# --------------------------------------------------------------------------

CHANNELS = [
    {
        "name": "Canal 1",
        "link": "https://t.me/+5QUaalkR6t00NjY5",
        "chat_id": os.getenv("CHANNEL_1_ID", "-1003828879197"),  # a remplacer
    },
    {
        "name": "Canal 2",
        "link": "https://t.me/INFERNOxOTP",
        "chat_id": os.getenv("CHANNEL_2_ID", "-1003724798018"),
    },
    {
        "name": "Canal 3",
        "link": "https://t.me/+oy1Jh6Xc5HFiZjE0",
        "chat_id": os.getenv("CHANNEL_3_ID", "-1004390236547"),  # a remplacer
    },
]

# Footer obligatoire sur tous les messages du bot
FOOTER = "\n\n⚡ Powered By LUST 欲 ❤️"

# Limite Telegram pour l'envoi de fichiers vidéo via le Bot API classique (Mo)
MAX_TELEGRAM_FILE_SIZE_MB = 50

# Anti-spam : délai minimum (secondes) entre deux requêtes d'un même utilisateur
ANTI_SPAM_COOLDOWN = 5

# Dossier de téléchargement temporaire
DOWNLOAD_DIR = "downloads"

# Base de données SQLite (historique + statistiques)
DB_PATH = "lust_bot.db"

# Qualités vidéo proposées à l'utilisateur lorsqu'elles sont disponibles
SUPPORTED_QUALITIES = [360, 480, 720, 1080]
