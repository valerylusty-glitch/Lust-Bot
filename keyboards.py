"""
Construction des claviers inline utilisés par le bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DEV_COMMUNITY_LINK


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Télécharger Vidéo", callback_data="menu_download")],
        [
            InlineKeyboardButton("📜 Historique", callback_data="menu_history"),
            InlineKeyboardButton("📊 Statistiques", callback_data="menu_stats"),
        ],
        [
            InlineKeyboardButton("ℹ️ Aide", callback_data="menu_help"),
            InlineKeyboardButton("👨‍💻 Développeur", callback_data="menu_dev"),
        ],
        [InlineKeyboardButton("🔄 Actualiser", callback_data="menu_refresh")],
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Retour au menu", callback_data="menu_refresh")]
    ])


def developer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Communauté", url=DEV_COMMUNITY_LINK)],
        [InlineKeyboardButton("⬅️ Retour au menu", callback_data="menu_refresh")],
    ])


def quality_keyboard(qualities: list, token: str) -> InlineKeyboardMarkup:
    """Clavier de sélection de qualité. `token` identifie la requête de
    téléchargement en attente (stockée temporairement en mémoire)."""
    buttons = []
    row = []
    for q in qualities:
        row.append(InlineKeyboardButton(f"{q}p", callback_data=f"quality_{token}_{q}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⭐ Meilleure qualité", callback_data=f"quality_{token}_best")])
    return InlineKeyboardMarkup(buttons)
