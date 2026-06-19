"""
Vérification de l'abonnement obligatoire (Force Subscribe) aux canaux
définis dans config.CHANNELS.
"""

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from config import CHANNELS

logger = logging.getLogger(__name__)

VALID_STATUSES = {"member", "administrator", "creator"}


async def is_user_subscribed(bot, user_id: int) -> bool:
    """Vérifie que l'utilisateur est membre de TOUS les canaux requis."""
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in VALID_STATUSES:
                return False
        except TelegramError as e:
            logger.warning(f"Impossible de verifier l'abonnement a {channel['name']} : {e}")
            return False
    return True


def build_subscribe_keyboard() -> InlineKeyboardMarkup:
    """Construit le clavier avec un bouton par canal + le bouton Verifier."""
    buttons = []
    for channel in CHANNELS:
        buttons.append([InlineKeyboardButton(f"Rejoindre {channel['name']}", url=channel["link"])])
    buttons.append([InlineKeyboardButton("Verifier", callback_data="check_subscription")])
    return InlineKeyboardMarkup(buttons)

